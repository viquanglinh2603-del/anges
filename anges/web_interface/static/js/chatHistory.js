const {
    AppBar, Toolbar, Typography, Button, TextField,
    Paper, Container, Box, CircularProgress, Select, MenuItem,
    FormControl, InputLabel, Collapse, Drawer, List, ListItem, ListItemText,
    IconButton, Dialog, DialogTitle, DialogContent, DialogActions
} = MaterialUI;

function useChatHistory() {
    const [showChatHistory, setShowChatHistory] = React.useState(false);
    const [chatHistory, setChatHistory] = React.useState([]);
    const [editDialogOpen, setEditDialogOpen] = React.useState(false);
    const [editingChatId, setEditingChatId] = React.useState(null);
    const [editingTitle, setEditingTitle] = React.useState('');
    const [selectedChat, setSelectedChat] = React.useState(null);

    const fetchChatHistory = async () => {
        try {
            const response = await fetch('/list-chats');
            const data = await response.json();
            if (data.status === 'success') {
                const chatsArray = Object.values(data.chats);
                setChatHistory(chatsArray);
            }
        } catch (error) {
            console.error('Error fetching chat history:', error);
        }
    };

    const handleChatSelect = async (chatId, setMessages, setIsLoading) => {
        if (!setMessages || !setIsLoading) {
            console.error('Missing required handlers for chat selection');
            return false;
        }

        setIsLoading(true);
        setSelectedChat(chatId);
        try {
            const response = await fetch(`/load-chat/${chatId}`);
            const data = await response.json();
            if (data.status === 'success') {
                // Transform events into message format
                const messages = data.events.map(event => ({
                    type: ["new_request", "follow_up_request"].includes(event.type) ? 'user' : 'agent',
                    content: event.content || event.message
                }));
                setMessages(messages);
                return true;
            }
        } catch (error) {
            console.error('Error loading chat:', error);
        } finally {
            setIsLoading(false);
        }
        return false;
    };

    const handleEditClick = (chatId, title) => {
        setEditingChatId(chatId);
        setEditingTitle(title || '');  // Handle null/undefined title
        setEditDialogOpen(true);
    };

    const handleEditSubmit = async () => {
        if (!editingChatId) return;

        // Validate title before sending
        const trimmedTitle = editingTitle ? editingTitle.trim() : '';
        if (!trimmedTitle) {
            console.error('Title cannot be empty');
            return;
        }

        try {
            const response = await fetch(`/edit-chat/${editingChatId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: trimmedTitle })
            });
        
            // First, check if the response has an HTTP error status.
            if (!response.ok) {
                alert(`Failed to update chat title: ${response.status} - ${response.statusText}`);
                return;
            }
        
            const data = await response.json();
            
            // Check if the server-side logic returned a success status.
            if (data.status === 'success') {
                await fetchChatHistory();
                setEditDialogOpen(false);
                setEditingChatId(null);
                setEditingTitle('');
            } else {
                // If it's a non-success response, show the message or a fallback.
                console.error('Failed to update chat title:', data.message);
                alert(`Failed to update chat title: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            // Catch network/other errors
            console.error('Error updating chat title:', error);
            alert(`Error updating chat title: ${error.message}`);
        }
        
    };

    const handleDeleteClick = async (chatId) => {
        if (window.confirm('Are you sure you want to delete this chat?')) {
            try {
                const response = await fetch(`/delete-chat/${chatId}`, {
                    method: 'POST',
                });
    
                // Check if the response is not OK
                if (!response.ok) {
                    alert(`Failed to delete chat: ${response.status} - ${response.statusText}`);
                    return false;
                }
    
                const data = await response.json();
    
                // Check the returned data's status
                if (data.status === 'success') {
                    await fetchChatHistory();
                    if (selectedChat === chatId) {
                        setSelectedChat(null);
                    }
                    return true;
                } else {
                    // If the response is OK but data.status !== 'success'
                    alert(`Failed to delete chat: ${data.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error deleting chat:', error);
                alert(`Error deleting chat: ${error.message}`);
            }
        }
        return false;
    };
    

    React.useEffect(() => {
        fetchChatHistory();
        const interval = setInterval(fetchChatHistory, 30000);
        return () => clearInterval(interval);
    }, []);

    return {
        showChatHistory, setShowChatHistory,
        chatHistory, setChatHistory,
        editDialogOpen, setEditDialogOpen,
        editingChatId, setEditingChatId,
        editingTitle, setEditingTitle,
        selectedChat, setSelectedChat,
        handleChatSelect,
        handleEditClick,
        handleEditSubmit,
        handleDeleteClick,
        fetchChatHistory
    };
}
