import React, { memo } from 'react';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2 } from 'lucide-react';

// Define needed props directly
interface SidebarItemProps {
    exchangeId: number;
    title: string; // e.g., person's name or "Unknown Contact"
    messagePreview: string;
    time: string;
    sourceFile: string; // Still useful for display or debugging
    // internalExchangeIndex: number; // May not be needed if exchangeId is primary key

    isSelected: boolean;
    onClick: (exchangeId: number) => void;
    onClear: () => void; // Simplified: parent knows which one to clear

    isMergeModeActive: boolean;
    isSelectedForMerge: boolean;
    onToggleMergeSelection: (exchangeId: number, sourceFile: string) => void;
    isMergeCompatible?: boolean; // Make optional, parent can decide
}

// Use React.memo to prevent unnecessary re-renders
const SidebarItem = memo(({
    exchangeId,
    title,
    messagePreview,
    time,
    sourceFile,
    // internalExchangeIndex,
    isSelected,
    onClick,
    onClear,
    isMergeModeActive,
    isSelectedForMerge,
    onToggleMergeSelection,
    isMergeCompatible = true
}: SidebarItemProps) => {
    // console.log(`SidebarItem rendering: exchangeId ${exchangeId}`);

    if (!title && !messagePreview) { // Simplified check for an "empty" item representation
        return (
            <div className={`flex items-center p-3 cursor-pointer hover:bg-gray-100 ${isSelected ? "bg-[#f0f2f5]" : ""} ${!isMergeCompatible ? 'opacity-50' : ''}`}>
                {isMergeModeActive && (
                    <Checkbox
                        id={`merge-${exchangeId}`}
                        checked={isSelectedForMerge}
                        disabled={!isMergeCompatible}
                        onCheckedChange={() => onToggleMergeSelection(exchangeId, sourceFile)}
                        className="mr-3"
                        aria-label="Select chat for merging"
                    />
                )}
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-500 truncate">Chat Cleared or Empty</p>
                    <p className="text-xs text-gray-400 truncate">(Source: {sourceFile})</p>
                </div>
                 <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onClear();
                    }}
                    className="ml-2 text-red-500 hover:text-red-700 opacity-50 hover:opacity-100"
                    aria-label="Clear chat data"
                 >
                     <Trash2 className="h-4 w-4" />
                 </button>
            </div>
        );
    }

    // For Avatar, use initials from title or a default. Avatar image can be generic or based on title/ID.
    const initials = title ? title.substring(0, 2).toUpperCase() : "??";
    // const avatarUrl = "/avatars/default.png"; // Or logic to pick one

    return (
        <div
            className={`flex items-center p-3 cursor-pointer hover:bg-gray-100 ${isSelected ? "bg-[#f0f2f5]" : ""} ${isMergeModeActive && !isMergeCompatible ? 'opacity-50' : ''}`}
            onClick={() => {
              if (isMergeModeActive) {
                if (isMergeCompatible) {
                  onToggleMergeSelection(exchangeId, sourceFile);
                }
                // If not compatible, click does nothing in merge mode on the item itself
              } else {
                onClick(exchangeId); // Default action: view chat
              }
            }}
        >
            {isMergeModeActive && (
                 <Checkbox
                    id={`merge-${exchangeId}`}
                    checked={isSelectedForMerge}
                    disabled={!isMergeCompatible}
                    className="mr-3 pointer-events-none"
                    aria-label="Select chat for merging"
                 />
            )}
            <Avatar className="h-12 w-12 mr-3 flex-shrink-0">
                <AvatarFallback className="bg-gray-200 text-gray-700">{initials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{title}</p>
                <p className="text-xs text-gray-500 truncate">{messagePreview}</p>
            </div>
            <div className="flex flex-col items-end ml-2 flex-shrink-0">
                <p className="text-xs text-gray-400 whitespace-nowrap">{time}</p>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onClear();
                    }}
                    className="mt-1 text-red-500 hover:text-red-700 opacity-50 hover:opacity-100"
                    aria-label="Clear chat data"
                >
                    <Trash2 className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
});

SidebarItem.displayName = 'SidebarItem';

export default SidebarItem; 