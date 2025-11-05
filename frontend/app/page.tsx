"use client"

import { useState, useEffect, useRef, useMemo, useCallback, Fragment } from "react"
import { ChevronLeft, MoreVertical, Trash2, X } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import SidebarItem from "./components/SidebarItem"
import MessageBubble from "./components/MessageBubble"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"

// Define interfaces for the data structure to match API
export interface Message {
  message_id?: number;
  date: string;
  time: string;
  person: string;
  quote: string;
}

export interface ExchangeWithSource {
  sourceFile: string;
  internalIndex: number;
  messages: Message[];
  exchange_id?: number;
  id?: number;
}

interface WhatsAppContent {
  cute_exchanges: ExchangeWithSource[];
}

interface PaginationInfo {
  currentPage: number;
  pageSize: number;
  totalExchanges: number;
  hasMore: boolean;
}

interface WhatsAppData {
  content: WhatsAppContent;
  pagination: PaginationInfo;
}

// Default page size constant
const PAGE_SIZE = 20;

export default function WhatsAppClone() {
  // --- State --- 
  const [whatsAppData, setWhatsAppData] = useState<WhatsAppData | null>(null);
  const [selectedExchangeId, setSelectedExchangeId] = useState<number | null>(null);
  const [selectedMessages, setSelectedMessages] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [exchangeToDelete, setExchangeToDelete] = useState<{ exchangeId: number; sourceFile?: string; internalIndex?: number } | null>(null);
  const [mobileView, setMobileView] = useState<'list' | 'chat'>('list');
  const [isMergeModeActive, setIsMergeModeActive] = useState(false);
  const [selectedForMerge, setSelectedForMerge] = useState<Set<number>>(new Set());
  const [isMergeConfirmDialogOpen, setIsMergeConfirmDialogOpen] = useState(false);
  const [mergeTargetSourceFile, setMergeTargetSourceFile] = useState<string | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const [currentExchangeDetails, setCurrentExchangeDetails] = useState<ExchangeWithSource | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  // -----------------------------

  // --- Callbacks & Handlers ---

  const fetchData = useCallback(async (page = 1) => {
    if (page === 1) {
      setIsLoading(true);
      setSelectedExchangeId(null);
      setCurrentExchangeDetails(null); // Clear details when re-fetching main list
      setWhatsAppData(null);
    } else {
      setIsFetchingMore(true);
    }
    setError(null);

    try {
      const response = await fetch(`/api/messages?page=${page}&pageSize=${PAGE_SIZE}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown'}`);
      }
      const newData: WhatsAppData = await response.json();

      setWhatsAppData(prevData => {
        const newExchanges = newData.content.cute_exchanges.map(ex => ({ ...ex, messages: ex.messages || [] }));
        if (page === 1 || !prevData) {
          return { ...newData, content: { cute_exchanges: newExchanges } };
        } else {
          return {
            content: {
              cute_exchanges: [
                ...prevData.content.cute_exchanges,
                ...newExchanges
              ]
            },
            pagination: newData.pagination
          };
        }
      });
    } catch (e: any) {
      setError(e instanceof Error ? e.message : "An unknown error occurred");
      if (page === 1) {
        setWhatsAppData(null);
      }
    } finally {
      if (page === 1) {
        setIsLoading(false);
      } else {
        setIsFetchingMore(false);
      }
    }
  }, []);

  const toggleMessageSelection = useCallback((backendMessageId: number) => {
    setSelectedMessages((prev) => {
      const newSelection = new Set(prev);
      if (newSelection.has(backendMessageId)) {
        newSelection.delete(backendMessageId);
      } else {
        newSelection.add(backendMessageId);
      }
      return newSelection;
    });
  }, []);

  const handleSelectExchange = useCallback(async (exchangeId: number | null) => {
    if (exchangeId === null) {
      setSelectedExchangeId(null);
      setCurrentExchangeDetails(null);
      setMobileView('list');
      return;
    }
    
    setSelectedExchangeId(exchangeId);
    setMobileView('chat');
    setSelectedMessages(new Set());
    setIsLoadingDetails(true);
    setCurrentExchangeDetails(null);
    setError(null);

    if (typeof window !== 'undefined') {
      window.history.pushState({ view: 'chat', exchangeId: exchangeId }, '');
    }

    try {
      const response = await fetch(`/api/exchanges/${exchangeId}`); 
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Failed to load exchange details'}`);
      }
      const data: ExchangeWithSource = await response.json();
      setCurrentExchangeDetails({...data, exchange_id: data.id ?? data.exchange_id, messages: data.messages || []});
    } catch (e: any) {
      setError(e instanceof Error ? e.message : "An unknown error occurred while fetching details");
      setCurrentExchangeDetails(null);
    } finally {
      setIsLoadingDetails(false);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedMessages(new Set());
  }, []);

  const handleDeleteExchange = useCallback((exchangeIdToDelete: number, sourceFile?: string, internalIndex?: number) => {
    setExchangeToDelete({ exchangeId: exchangeIdToDelete, sourceFile, internalIndex });
    setIsDeleteDialogOpen(true);
  }, []);

  const confirmDeleteExchange = useCallback(async () => {
    if (!exchangeToDelete || exchangeToDelete.exchangeId === undefined) {
        alert("Error: Critical information missing for delete operation.");
        setIsDeleteDialogOpen(false);
        setExchangeToDelete(null);
        return;
    }
    const { exchangeId } = exchangeToDelete;
    
    setIsDeleteDialogOpen(false);
    try {
      const response = await fetch(`/api/exchanges/${exchangeId}`, {
        method: 'DELETE',
      });

      if (response.status === 204) {
        await fetchData(1); // Refetch main list
        if (selectedExchangeId === exchangeId) { 
          handleSelectExchange(null);
        }
      } else if (response.status === 404) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to delete chat: Chat not found (404). ${errorData.error || ''}`);
      } else if (!response.ok) {
        let errorDetail = 'Unknown server error';
        try {
            const result = await response.json();
            errorDetail = result.error || result.message || JSON.stringify(result);
        } catch (e) {
            errorDetail = response.statusText;
        }
        throw new Error(`Failed to delete chat: ${errorDetail} (Status: ${response.status})`);
      }
    } catch (error: any) {
      alert(`Failed to delete chat: ${error.message}`);
    } finally {
        setExchangeToDelete(null);
    }
  }, [exchangeToDelete, fetchData, selectedExchangeId, handleSelectExchange]);

  const deleteSelectedMessages = useCallback(async () => {
    if (selectedMessages.size === 0 || !currentExchangeDetails || currentExchangeDetails.exchange_id === undefined) {
      return;
    }

    const messageIdsToDelete = Array.from(selectedMessages);

    if (messageIdsToDelete.length === 0) {
      alert("No messages found to delete.");
      return;
    }

    try {
      const response = await fetch('/api/messages/delete', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_ids: messageIdsToDelete }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to delete messages: ${errorData.detail || response.statusText}`);
      }
      
      if (currentExchangeDetails.exchange_id !== undefined) {
        await handleSelectExchange(currentExchangeDetails.exchange_id);
      }
      setSelectedMessages(new Set()); // Clear selection
    } catch (e: any) {
      alert(`Failed to delete messages: ${e.message}`);
    }
  }, [selectedMessages, currentExchangeDetails, handleSelectExchange]);

  const handleToggleMergeSelection = useCallback((exchangeId: number, currentSourceFile: string) => {
    setSelectedForMerge(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(exchangeId)) {
        newSelection.delete(exchangeId);
        if (newSelection.size === 0) {
          setMergeTargetSourceFile(null);
        }
      } else {
        if (mergeTargetSourceFile === null) {
          setMergeTargetSourceFile(currentSourceFile);
          newSelection.add(exchangeId);
        } else if (mergeTargetSourceFile === currentSourceFile) {
          newSelection.add(exchangeId);
        } else {
          alert(`You can only merge chats from the same source file. The current selection is for chats from file: "${mergeTargetSourceFile}".`);
        }
      }
      return newSelection;
    });
  }, [mergeTargetSourceFile]);

  const confirmMergeExchanges = useCallback(async () => {
    if (selectedForMerge.size < 2) {
      alert("Please select at least two exchanges to merge.");
      return;
    }
    const idsToMerge = Array.from(selectedForMerge);
    setIsMergeConfirmDialogOpen(false);

    try {
      const response = await fetch('/api/exchanges/merge-multiple', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exchange_ids: idsToMerge }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to merge exchanges: ${errorData.detail || response.statusText}`);
      }
      setSelectedForMerge(new Set());
      setIsMergeModeActive(false);
      setMergeTargetSourceFile(null);
      await fetchData(1);
    } catch (error: any) {
      alert(`Failed to merge exchanges: ${error.message}`);
    }
  }, [selectedForMerge, fetchData]);

  // Effect to select first exchange after initial load completes (if screen width allows)
  useEffect(() => {
    if (!isLoading && selectedExchangeId === null && whatsAppData && 
        whatsAppData.content.cute_exchanges.length > 0 && 
        whatsAppData.pagination.currentPage === 1 &&
        typeof window !== 'undefined' && window.innerWidth >= 768) { // md breakpoint
      const firstExchangeId = whatsAppData.content.cute_exchanges[0].exchange_id;
      if (firstExchangeId !== undefined) {
        handleSelectExchange(firstExchangeId);
      }
    }
  }, [isLoading, whatsAppData, selectedExchangeId, handleSelectExchange]);

  // Initial data fetch - THIS ONE IS KEY
  useEffect(() => {
    fetchData(1);
  }, [fetchData]);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && whatsAppData?.pagination.hasMore && !isFetchingMore && !isLoading) {
          fetchData(whatsAppData.pagination.currentPage + 1);
        }
      },
      { threshold: 1.0 }
    );
    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }
    return () => {
      if (loadMoreRef.current) {
        observer.unobserve(loadMoreRef.current);
      }
    };
  }, [fetchData, whatsAppData, isFetchingMore, isLoading]);

  // Handle back button for mobile view
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      if (event.state?.view === 'list') {
        setMobileView('list');
        setSelectedExchangeId(null);
        setCurrentExchangeDetails(null);
      } else if (event.state?.view === 'chat' && event.state?.exchangeId !== undefined) {
        setMobileView('chat');
        if (selectedExchangeId !== event.state.exchangeId) {
             handleSelectExchange(event.state.exchangeId);
        }
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [selectedExchangeId, handleSelectExchange]); // Added handleSelectExchange dependency
  
  // --- Derived State / Memos ---
  const exchanges = useMemo(() => whatsAppData?.content?.cute_exchanges || [], [whatsAppData]);

  // currentExchange now primarily relies on currentExchangeDetails for the active chat.
  // It falls back to data from the main list for initial rendering or if details are missing.
  const currentExchange = useMemo(() => {
    if (selectedExchangeId === null) {
      return null;
    }
    
    if (currentExchangeDetails && currentExchangeDetails.exchange_id === selectedExchangeId) {
      return currentExchangeDetails;
    }
    
    const fallback = exchanges.find(ex => ex.exchange_id === selectedExchangeId) || null;
    return fallback;
  }, [selectedExchangeId, currentExchangeDetails, exchanges]);

  // Determine the "reference person" (first person in the exchange) for styling
  const referencePerson = useMemo(() => {
    if (!currentExchange?.messages || currentExchange.messages.length === 0) {
      return null;
    }
    return currentExchange.messages[0].person;
  }, [currentExchange]);

  const messagesByDate = useMemo(() => {
    if (!currentExchange?.messages) {
      return {};
    }

    const groupedMessages = currentExchange.messages.reduce<Record<string, Message[]>>((acc, msg, index) => {
      const date = msg.date || "Unknown Date";
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(msg);
      return acc;
    }, {});
    return groupedMessages;
  }, [currentExchange]);

  // Scroll to bottom of messages
  useEffect(() => {
    if (currentExchangeDetails && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentExchangeDetails?.messages]); // Trigger on messages change in details

  // --- Early Returns for Loading/Error States ---
  if (isLoading && !isFetchingMore) return <div className="flex justify-center items-center h-screen"><div>Loading chats...</div></div>;
  if (error && !whatsAppData) return <div className="flex justify-center items-center h-screen text-red-500">Error: {error}</div>;
  if (!whatsAppData && !isLoading) return <div className="flex justify-center items-center h-screen">No chats found.</div>;

  // --- Main Render ---
  return (
    <div className="flex h-screen antialiased text-gray-800 overflow-hidden">
      {/* Sidebar */}
      <div className={`flex flex-col w-full md:w-1/3 lg:w-1/4 border-r border-gray-300 bg-gray-100 flex-shrink-0 ${mobileView === 'chat' ? 'hidden md:flex' : 'flex'}`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-3 border-b h-16 flex-shrink-0 bg-white">
          <h1 className="text-xl font-semibold">Chats</h1>
          <div className="flex items-center space-x-2">
            {isMergeModeActive ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsMergeModeActive(false);
                    setSelectedForMerge(new Set());
                    setMergeTargetSourceFile(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setIsMergeConfirmDialogOpen(true)}
                  disabled={selectedForMerge.size < 2}
                >
                  Merge ({selectedForMerge.size})
                </Button>
              </>
            ) : (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem 
                    onSelect={() => {
                      setIsMergeModeActive(true);
                    }}
                  >
                    Start Merge Mode
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
        {/* Chat List */}
        <div className="flex-grow overflow-y-auto bg-white">
          {exchanges.map((exchange) => {
            if (exchange.exchange_id === undefined) return null; // Should not happen with backend data
            
            const firstMessage = exchange.messages && exchange.messages.length > 0 ? exchange.messages[0] : undefined;
            const title = firstMessage?.person || "Unknown Contact";
            const messagePreview = firstMessage?.quote || (exchange.messages.length === 0 && currentExchangeDetails?.exchange_id === exchange.exchange_id && !isLoadingDetails ? "Chat is empty" : "No messages");
            const time = firstMessage?.time || "";

            // Determine if this item is compatible for merging based on sourceFile
            let isMergeCompatible = true; 
            if (isMergeModeActive) {
              if (mergeTargetSourceFile === null) {
                isMergeCompatible = true;
              } else {
                isMergeCompatible = exchange.sourceFile === mergeTargetSourceFile || selectedForMerge.has(exchange.exchange_id!);
              }
            }

            return (
              <SidebarItem
                key={exchange.exchange_id}
                exchangeId={exchange.exchange_id}
                title={title}
                messagePreview={messagePreview}
                time={time}
                sourceFile={exchange.sourceFile} // Keep for display or debug if needed
                isSelected={selectedExchangeId === exchange.exchange_id}
                onClick={handleSelectExchange} // handleSelectExchange now takes exchangeId
                onClear={() => handleDeleteExchange(exchange.exchange_id!, exchange.sourceFile, exchange.internalIndex)} // Updated to call handleDeleteExchange
                isMergeModeActive={isMergeModeActive}
                isSelectedForMerge={selectedForMerge.has(exchange.exchange_id!)}
                onToggleMergeSelection={(id) => handleToggleMergeSelection(id, exchange.sourceFile)} // Pass sourceFile here
                isMergeCompatible={isMergeCompatible}
              />
            );
          })}
          {isFetchingMore && <div className="text-center p-4">Loading more chats...</div>}
          <div ref={loadMoreRef} style={{ height: "1px" }} />
          {error && <div className="p-4 text-red-500">Error loading more: {error}</div>}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className={`flex flex-col flex-grow w-full md:w-2/3 lg:w-3/4 bg-[#e5ddd5] ${mobileView === 'list' ? 'hidden md:flex' : 'flex'}`}>
        {selectedExchangeId === null && !isLoadingDetails ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <MoreVertical size={64} className="text-gray-400 mb-4" /> {/* Lucide MoreVertical */} 
            <p className="text-lg font-medium text-gray-600">Select a chat to start messaging</p>
            <p className="text-sm text-gray-500">Choose one from the sidebar or start a new one (if feature exists).</p>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className="bg-[#f0f2f5] p-3 flex items-center border-b h-16 flex-shrink-0">
             {selectedMessages.size > 0 ? (
                <>
                  <button onClick={clearSelection} className="mr-4 text-gray-600 hover:text-gray-800">
                    <X className="h-6 w-6" />
                  </button>
                  <div className="flex-1">
                   <h2 className="font-medium">{selectedMessages.size} selected</h2>
                  </div>
                  <button 
                    onClick={deleteSelectedMessages} 
                    className="text-red-500 hover:text-red-700" 
                    disabled={!currentExchangeDetails || selectedMessages.size === 0}
                  >
                    <Trash2 className="h-6 w-6" />
                  </button>
                </>
             ) : currentExchange ? (
                <>
                  <div className="md:hidden mr-2" onClick={() => handleSelectExchange(null) /* Effectively goes to list view */ }>
                    <ChevronLeft className="h-6 w-6 text-gray-600 cursor-pointer" />
                  </div>
                  <Avatar className="h-10 w-10 mr-3">
                   <AvatarFallback className="bg-gray-200 text-gray-700">
                     {currentExchange.messages[0]?.person?.substring(0, 2).toUpperCase() || currentExchange.sourceFile?.substring(0,2).toUpperCase() || "??"}
                   </AvatarFallback>
                  </Avatar>
                 <div className="flex-grow">
                   <h2 className="font-semibold">
                     {currentExchange.messages[0]?.person || currentExchange.sourceFile || "Chat"}
                   </h2>
                 </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-6 w-6 text-gray-600" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem 
                        onSelect={(e) => {
                            e.preventDefault();
                            if (currentExchange && currentExchange.exchange_id !== undefined) {
                                handleDeleteExchange(currentExchange.exchange_id, currentExchange.sourceFile, currentExchange.internalIndex); // Updated to call handleDeleteExchange
                            }
                        }}
                        className="text-red-500"
                      >
                        Delete Chat
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
             ) : isLoadingDetails ? (
                <div className="flex items-center justify-center w-full"><p>Loading chat...</p></div>
             ) : (
                <div className="flex items-center justify-center w-full"><p>Select a chat</p></div>
             )}
            </div>

            {/* Messages Area */}
            <div 
              className="flex-grow overflow-y-auto p-4 space-y-2"
              style={{ backgroundImage: "url('/background.png')", backgroundRepeat: 'repeat' }}
            >
            {isLoadingDetails && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
                <p>Loading messages...</p>
              </div>
            )}
            {!currentExchangeDetails && !isLoadingDetails && selectedExchangeId !== null && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-lg font-medium text-gray-500">Error loading messages or chat not found.</p>
              </div>
            )}
            {currentExchangeDetails && currentExchangeDetails.messages && currentExchangeDetails.messages.length === 0 && !isLoadingDetails && (
               <div className="flex flex-col items-center justify-center h-full text-center">
                <MoreVertical size={64} className="text-gray-400 mb-4" /> {/* Changed Icon */}
                <p className="text-lg font-medium text-gray-500">No messages in this exchange.</p>
                <p className="text-sm text-gray-400">It might have been cleared or is new.</p>
              </div>
            )}
            {currentExchangeDetails && currentExchangeDetails.messages && currentExchangeDetails.messages.length > 0 && (
              Object.entries(messagesByDate).map(([date, messagesInDate]) => {
                return (
                  <Fragment key={date}>
                    <div className="text-center my-2">
                      <span className="px-2 py-1 text-xs bg-white rounded-md shadow">{date}</span>
                    </div>
                    {messagesInDate.map((message, msgIndex) => {
                      if (message.message_id === undefined) {
                        return null; // Cannot process without id
                      }

                      const isOwn = message.person === referencePerson;
                      const isSelected = selectedMessages.has(message.message_id!);
                      const nextMessage = msgIndex + 1 < messagesInDate.length ? messagesInDate[msgIndex + 1] : null;
                      const isLastInSequence = !nextMessage || nextMessage.person !== message.person || nextMessage.time !== message.time; // Simplified sequence check for tail
                      
                      return (
                        <MessageBubble
                          key={message.message_id} 
                          message={message} // Pass the full message object
                          isOwn={isOwn}
                          isSelected={isSelected}
                          onToggleSelect={toggleMessageSelection} // toggleMessageSelection expects message_id
                          isLastInSequence={isLastInSequence} 
                        />
                      );
                    })}
                  </Fragment>
                );
              })
            )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Area - Placeholder */}
            <div className="bg-[#f0f2f5] p-3 flex items-center flex-shrink-0 border-t h-16">
              <div className="bg-white rounded-full flex-1 p-2 px-4 text-gray-400">
               {selectedMessages.size > 0 
                 ? `${selectedMessages.size} message(s) selected` 
                 : (currentExchangeDetails ? "Type a message..." : "Select a chat to type")
                }
              </div>
            </div>
          </>
        )}
      </div>
      {/* Merge Confirmation Dialog */}
      <AlertDialog open={isMergeConfirmDialogOpen} onOpenChange={setIsMergeConfirmDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Merge</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to merge the selected {selectedForMerge.size} chats?
              Their messages will be combined into a single chat. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedForMerge(new Set())}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmMergeExchanges}>Merge</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Exchange Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chat?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this chat (ID: {exchangeToDelete?.exchangeId})? 
              All its messages will be permanently removed. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteExchange}>Delete Chat</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
