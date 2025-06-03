// Function to complete a quest
async function completeQuest(taskIndex) {
    try {
        const response = await fetch('/api/complete_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task_index: taskIndex })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Refresh the page to show updated stats and quests
            location.reload();
        } else {
            alert('Failed to complete quest: ' + data.error);
        }
    } catch (error) {
        console.error('Error completing quest:', error);
        alert('Failed to complete quest. Please try again.');
    }
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