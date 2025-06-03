// Function to complete a quest
async function completeQuest(taskIndex, questName) {
    try {
        const response = await fetch('/api/complete_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                task_index: taskIndex,
                quest_name: questName 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show the notification in a modal overlay
            showNotificationModal(data.notification);
            
            // After notification timeout, refresh the page
            setTimeout(() => {
                location.reload();
            }, 5000);
        } else {
            alert('Failed to complete quest: ' + data.error);
        }
    } catch (error) {
        console.error('Error completing quest:', error);
        alert('Failed to complete quest. Please try again.');
    }
}

// Function to show notification modal
function showNotificationModal(notification) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-80';
    
    // Create notification content
    const content = `
        <div class="w-[420px] p-8 notification-container">
            <h2 class="notification-header mb-4">
                <span class="mr-2">⚡</span> NOTIFICATION
            </h2>

            <div class="notification-type mb-2">
                [${notification.type}:]
            </div>
            <div class="notification-message mb-6">
                "${notification.message}"
            </div>

            <div class="flex justify-center items-center">
                <div class="check-icon-wrapper">
                    <svg class="check-icon" viewBox="0 0 24 24">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
            </div>
        </div>
    `;
    
    overlay.innerHTML = content;
    document.body.appendChild(overlay);
    
    // Remove overlay after 5 seconds
    setTimeout(() => {
        overlay.remove();
    }, 5000);
}

// Function to get quest suggestions
async function suggestQuests() {
    try {
        const response = await fetch('/api/suggest_tasks');
        const data = await response.json();
        
        // Refresh the page to show new quests
        location.reload();
    } catch (error) {
        console.error('Error getting quest suggestions:', error);
        alert('Failed to get quest suggestions. Please try again.');
    }
}

// Function to toggle completed quests visibility
function toggleCompletedQuests() {
    const completedSection = document.querySelector('.completed-quests-section');
    const button = document.querySelector('.history-btn');
    
    if (completedSection.style.display === 'none') {
        completedSection.style.display = 'block';
        button.textContent = 'Hide History';
    } else {
        completedSection.style.display = 'none';
        button.textContent = 'Show History';
    }
}

// Function to create a custom notification
async function createNotification(type, message) {
    try {
        const response = await fetch('/api/notify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, message })
        });
        
        const data = await response.json();
        
        if (data.success && data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        console.error('Error creating notification:', error);
    }
}

// Add animation when quest cards appear
document.addEventListener('DOMContentLoaded', () => {
    const questCards = document.querySelectorAll('.quest-card');
    questCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}); 