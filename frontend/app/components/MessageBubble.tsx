import React, { memo } from 'react';

// Define needed types locally or import from a shared types file if created
interface Message { // This can be imported from a shared types definition if available
    message_id?: number; // Added message_id, it's crucial for selection
    date: string;
    time: string;
    person: string;
    quote: string;
}

interface MessageBubbleProps {
    message: Message; // Pass the whole message object
    isOwn: boolean; // True if the current user sent the message
    isSelected: boolean;
    onToggleSelect?: (messageId: number) => void; // Callback with backend message_id, optional
    isLastInSequence: boolean; // Retained for tail rendering logic
}

const MessageBubble = memo(({
    message,
    isOwn,
    isSelected,
    onToggleSelect,
    isLastInSequence
}: MessageBubbleProps) => {
    const handleToggle = () => {
        if (onToggleSelect && message.message_id !== undefined) {
            onToggleSelect(message.message_id);
        }
    };

    const baseBubbleClasses = "rounded-lg";
    let variantClasses = isOwn
        ? "bg-white text-gray-800 self-end"
        : "bg-whatsapp-message-green text-gray-800 self-start"; // Assuming whatsapp-message-green is defined, e.g., like #dcf8c6

    const outgoingTail = "relative after:content-[''] after:absolute after:bottom-[1px] after:right-[-7px] after:w-0 after:h-0 after:border-t-[10px] after:border-t-transparent after:border-l-[10px] after:border-l-white after:border-b-[0px] after:border-b-transparent after:rotate-[10deg]";
    const incomingTail = "relative before:content-[''] before:absolute before:bottom-[1px] before:left-[-7px] before:w-0 before:h-0 before:border-t-[10px] before:border-t-transparent before:border-r-[10px] before:border-r-whatsapp-message-green before:border-b-[0px] before:border-b-transparent before:-rotate-[10deg]";
    
    const tailClasses = isLastInSequence ? (isOwn ? outgoingTail : incomingTail) : "";

    return (
        <div
            className={`flex mb-2 group ${isOwn ? "justify-end" : "justify-start"}`}
            onClick={handleToggle} // Allow clicking the whole bubble to toggle selection
        >
            <div
                className={[
                  "max-w-[70%]", "px-3", "py-2", "shadow-sm", "cursor-pointer", "transition-all",
                  baseBubbleClasses,
                  variantClasses,
                  tailClasses,
                  isSelected ? "ring-2 ring-blue-500 ring-offset-1 ring-offset-[#e5ddd5]" : "",
                ].join(" ").trim()}
            >
                <p className="text-xs font-semibold text-gray-600 mb-1">{message.person}</p>
                <p className="text-sm whitespace-pre-wrap break-words">{message.quote}</p>
                <p className="text-right text-xs text-gray-500 mt-1">{message.time}</p>
            </div>
        </div>
    );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble; 