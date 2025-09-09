/**
 * Centralized Matrix Rain Animation System
 * Provides consistent matrix rain effects across all pages
 */

class MatrixRain {
    constructor(containerId = 'binary-background') {
        this.containerId = containerId;
        this.container = null;
        this.intervalId = null;
        this.isRunning = false;
        
        // Uniform parameters for consistent behavior
        this.config = {
            chars: ['0', '1'],
            frequency: 0.97, // Math.random() > 0.97 (3% spawn chance)
            animationDurationMin: 3, // seconds (faster)
            animationDurationMax: 6, // seconds (faster)
            spawnInterval: 100, // milliseconds (more frequent)
            characterLifetime: 6000, // milliseconds (shorter lifetime)
            columnWidth: 20, // pixels
            color: 'rgba(34, 197, 94, 0.4)', // Green matrix color
            textShadow: '0 0 5px rgba(34, 197, 94, 0.3)', // Green glow
            immediateVisibilityChance: 0.8 // 80% chance to start closer to screen
        };
    }

    init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.warn(`Matrix rain container '${this.containerId}' not found`);
            return false;
        }
        return true;
    }

    start() {
        if (!this.init() || this.isRunning) return;
        
        this.isRunning = true;
        this.container.style.display = 'block';
        
        // Create initial drops for immediate visibility
        for (let i = 0; i < 3; i++) {
            this.createDrop();
        }
        
        // Start continuous drop creation
        this.intervalId = setInterval(() => {
            this.createDrop();
        }, this.config.spawnInterval);
    }

    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        if (this.container) {
            this.container.style.display = 'none';
            this.container.innerHTML = ''; // Clear all characters
        }
    }

    createDrop() {
        if (!this.container) return;
        
        const columns = Math.floor(window.innerWidth / this.config.columnWidth);
        
        for (let i = 0; i < columns; i++) {
            if (Math.random() > this.config.frequency) {
                const char = this.createCharacter(i);
                this.container.appendChild(char);
                
                // Auto-remove after lifetime
                setTimeout(() => {
                    if (char.parentNode) {
                        char.parentNode.removeChild(char);
                    }
                }, this.config.characterLifetime);
            }
        }
    }

    createCharacter(columnIndex) {
        const char = document.createElement('div');
        char.className = 'binary-char';
        char.textContent = this.config.chars[Math.floor(Math.random() * this.config.chars.length)];
        
        // Position
        char.style.left = (columnIndex * this.config.columnWidth) + 'px';
        
        // Animation settings
        char.style.animationDelay = '0s';
        char.style.animationDuration = (
            Math.random() * (this.config.animationDurationMax - this.config.animationDurationMin) + 
            this.config.animationDurationMin
        ) + 's';
        
        // Layering
        char.style.zIndex = '-999';
        
        // Colors
        char.style.color = this.config.color;
        char.style.textShadow = this.config.textShadow;
        
        // Start position for immediate visibility
        const startPosition = Math.random() > this.config.immediateVisibilityChance ? 
            Math.random() * 10 + 'vh' :   // Most start ON SCREEN (immediate visibility)
            '-30vh';                       // Few start slightly above (quick appearance)
        char.style.top = startPosition;
        
        return char;
    }

    // Method to update configuration if needed
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
}

// Global instance for easy access
window.matrixRain = new MatrixRain();

// Convenience functions for backward compatibility
window.startMatrixRain = () => window.matrixRain.start();
window.stopMatrixRain = () => window.matrixRain.stop();
window.createMatrixRain = () => window.matrixRain.start(); // Alias for existing code
