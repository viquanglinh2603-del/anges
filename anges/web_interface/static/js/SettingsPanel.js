// anges/web_interface/static/js/SettingsPanel.js

// Assuming React is global or otherwise available (e.g. via <script> tag)
// Assuming MaterialUI is global or otherwise available (e.g. via <script> tag)

const {
    Drawer, Paper, Typography, TextField, Select, MenuItem,
    FormControl, InputLabel, Button, Modal, Box, List, ListItem,
    ListItemText, ListItemSecondaryAction, IconButton, Divider
} = MaterialUI;

function SettingsPanel({ coreState, onClose }) {
    // Add null check for coreState to prevent "Cannot read properties of undefined" error
    const modelType = coreState?.modelType || '';
    const agentType = coreState?.agentType || '';
    const workingDir = coreState?.workingDir || '';
    const prefixCmd = coreState?.prefixCmd || '';
    
    // Notes state management - ensure notes is always an array
    const rawNotes = coreState?.notes;
    const [notesModalOpen, setNotesModalOpen] = React.useState(false);
    const notes = Array.isArray(rawNotes) ? rawNotes : [];
    const [currentNote, setCurrentNote] = React.useState(null);
    const [noteForm, setNoteForm] = React.useState({
        title: '',
        content: '',
        scope: 'agent'
    });
    
    // Safely handle setters with null checks
    const handleModelChange = (e) => {
        if (coreState && coreState.setModelType) {
            coreState.setModelType(e.target.value);
        }
    };
    
    const handleAgentChange = (e) => {
        if (coreState && coreState.setAgentType) {
            coreState.setAgentType(e.target.value);
        }
    };
    
    const handleWorkingDirChange = (e) => {
        if (coreState && coreState.setWorkingDir) {
            coreState.setWorkingDir(e.target.value);
        }
    };
    
    const handlePrefixCmdChange = (e) => {
        if (coreState && coreState.setPrefixCmd) {
            coreState.setPrefixCmd(e.target.value);
        }
    };
    
    // Notes management functions
    const handleOpenNotesModal = () => {
        setNotesModalOpen(true);
        setCurrentNote(null);
        setNoteForm({ title: '', content: '', scope: 'agent' });
    };
    
    const handleCloseNotesModal = () => {
        setNotesModalOpen(false);
        setCurrentNote(null);
        setNoteForm({ title: '', content: '', scope: 'agent' });
    };
    
    const handleEditNote = (note) => {
        setCurrentNote(note);
        setNoteForm({
            title: note.title,
            content: note.content,
            scope: note.scope
        });
        setNotesModalOpen(true);
    };
    
    const handleSaveNote = () => {
        if (!noteForm.title.trim()) return;
        
        const newNote = {
            id: currentNote ? currentNote.id : Date.now().toString(),
            title: noteForm.title.trim(),
            content: noteForm.content.trim(),
            scope: noteForm.scope,
            timestamp: currentNote ? currentNote.timestamp : new Date().toISOString()
        };
        
        let updatedNotes;
        if (currentNote) {
            // Edit existing note
            updatedNotes = notes.map(note => 
                note.id === currentNote.id ? newNote : note
            );
        } else {
            // Add new note
            updatedNotes = [...notes, newNote];
        }
        
        // Update coreState.notes
        if (coreState && coreState.setNotes) {
            coreState.setNotes(updatedNotes);
        }
        
        handleCloseNotesModal();
    };
    
    const handleDeleteNote = (noteId) => {
        const updatedNotes = notes.filter(note => note.id !== noteId);
        if (coreState && coreState.setNotes) {
            coreState.setNotes(updatedNotes);
        }
    };
    
    const handleNoteFormChange = (field, value) => {
        setNoteForm(prev => ({
            ...prev,
            [field]: value
        }));
    };
    
    return React.createElement(MaterialUI.Drawer, {
        anchor: "right",
        open: coreState?.showSettings || false,
        onClose: undefined, // Disable onClose to prevent outside click closing
        variant: "persistent", // Use persistent variant to push content aside
        hideBackdrop: true, // Remove backdrop/overlay
        sx: {
            '& .MuiDrawer-paper': {
                zIndex: (theme) => theme.zIndex.drawer, // Ensure proper z-index below AppBar
            }
        }
    },
        React.createElement(Paper, {
            sx: {
                p: 3,
                pt: 11, // Add top padding to account for AppBar (64px + some extra spacing)
                width: 320,
                height: '100%', 
                overflow: 'auto'
            }
        },
            React.createElement(Typography, {
                variant: 'h6',
                sx: { mb: 2 }
            }, 'Settings'),
            
            // Model selection
            React.createElement(FormControl, { fullWidth: true, sx: { mb: 2 } },
                React.createElement(InputLabel, null, 'Model'),
                React.createElement(Select, {
                    value: modelType,
                    label: 'Model',
                    onChange: handleModelChange
                },
                    React.createElement(MenuItem, { value: 'agent_default' }, 'Default'),
                    React.createElement(MenuItem, { value: 'claude' }, 'Claude'),
                    React.createElement(MenuItem, { value: 'vertex_claude' }, 'VertexClaude'),
                    React.createElement(MenuItem, { value: 'gemini' }, 'Gemini'),
                    React.createElement(MenuItem, { value: 'openai' }, 'OpenAI'),
                    React.createElement(MenuItem, { value: 'deepseek' }, 'DeepSeek'),
                )
            ),
            
            // Agent Type selection
            React.createElement(FormControl, { fullWidth: true, sx: { mb: 2 } },
                React.createElement(InputLabel, null, 'Agent Type'),
                React.createElement(Select, {
                    value: agentType,
                    label: 'Agent Type',
                    onChange: handleAgentChange
                },
                    React.createElement(MenuItem, { value: 'default' }, 'Default'),
                    React.createElement(MenuItem, { value: 'task_executor' }, 'TaskExecutor'),
                    React.createElement(MenuItem, { value: 'task_analyzer' }, 'TaskAnalyzer'),
                    React.createElement(MenuItem, { value: 'orchestrator' }, 'Orchestrator')
                )
            ),
            
            // Working Directory
            React.createElement(TextField, {
                fullWidth: true,
                label: 'Working Directory',
                value: workingDir,
                onChange: handleWorkingDirChange,
                variant: 'outlined',
                sx: { mb: 2 }
            }),
            
            // Prefix Command
            React.createElement(TextField, {
                fullWidth: true,
                label: 'Prefix Command',
                value: prefixCmd,
                onChange: handlePrefixCmdChange,
                variant: 'outlined',
                sx: { mb: 3 }
            }),
            
            // Notes section
            React.createElement(Divider, { sx: { my: 3 } }),
            React.createElement(Box, {
                sx: { 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    mb: 2 
                }
            },
                React.createElement(Typography, {
                    variant: 'h6'
                }, 'Notes'),
                React.createElement(IconButton, {
                    size: 'small',
                    onClick: handleOpenNotesModal,
                    sx: { 
                        ml: 1,
                        color: 'primary.main'
                    }
                }, '+')
            ),
            
            // Notes list
            notes.length > 0 && React.createElement(List, { dense: true },
                notes.map(note => 
                    React.createElement(ListItem, { 
                        key: note.id,
                        sx: { px: 0 }
                    },
                        React.createElement(ListItemText, {
                            primary: note.title,
                            secondary: `Scope: ${note.scope}`,
                            primaryTypographyProps: { variant: 'body2' },
                            secondaryTypographyProps: { variant: 'caption' }
                        }),
                        React.createElement(ListItemSecondaryAction, null,
                            React.createElement(IconButton, {
                                size: 'small',
                                onClick: () => handleEditNote(note),
                                sx: { mr: 1 }
                            }, '✏️'),
                            React.createElement(IconButton, {
                                size: 'small',
                                onClick: () => handleDeleteNote(note.id)
                            }, '🗑️')
                        )
                    )
                )
            ),
            
            // Notes Modal
            React.createElement(Modal, {
                open: notesModalOpen,
                onClose: handleCloseNotesModal,
                ariaLabelledby: 'notes-modal-title'
            },
                React.createElement(Box, {
                    sx: {
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: 500,
                        bgcolor: 'background.paper',
                        border: '2px solid #000',
                        boxShadow: 24,
                        p: 4,
                        borderRadius: 1
                    }
                },
                    React.createElement(Typography, {
                        id: 'notes-modal-title',
                        variant: 'h6',
                        component: 'h2',
                        sx: { mb: 2 }
                    }, currentNote ? 'Edit Note' : 'Add New Note'),
                    
                    React.createElement(TextField, {
                        fullWidth: true,
                        label: 'Title',
                        value: noteForm.title,
                        onChange: (e) => handleNoteFormChange('title', e.target.value),
                        variant: 'outlined',
                        sx: { mb: 2 }
                    }),
                    
                    React.createElement(TextField, {
                        fullWidth: true,
                        label: 'Content',
                        value: noteForm.content,
                        onChange: (e) => handleNoteFormChange('content', e.target.value),
                        variant: 'outlined',
                        multiline: true,
                        rows: 4,
                        sx: { mb: 2 }
                    }),
                    
                    React.createElement(FormControl, { fullWidth: true, sx: { mb: 3 } },
                        React.createElement(InputLabel, null, 'Scope'),
                        React.createElement(Select, {
                            value: noteForm.scope,
                            label: 'Scope',
                            onChange: (e) => handleNoteFormChange('scope', e.target.value)
                        },
                            React.createElement(MenuItem, { value: 'agent' }, 'Agent'),
                            React.createElement(MenuItem, { value: 'global' }, 'Global')
                        )
                    ),
                    
                    React.createElement(Box, { sx: { display: 'flex', gap: 2, justifyContent: 'flex-end' } },
                        React.createElement(Button, {
                            onClick: handleCloseNotesModal
                        }, 'Cancel'),
                        React.createElement(Button, {
                            variant: 'contained',
                            onClick: handleSaveNote,
                            disabled: !noteForm.title.trim()
                        }, currentNote ? 'Update' : 'Add')
                    )
                )
            )
        )
    );
}

// Make SettingsPanel globally available
window.Anges = window.Anges || {};
window.Anges.SettingsPanel = SettingsPanel;
