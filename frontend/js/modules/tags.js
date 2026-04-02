class TagsAutocomplete {
    constructor(inputId, containerId, existingTags = []) {
        this.inputId = inputId;
        this.containerId = containerId;
        this.tags = [...existingTags];
        this.allTags = [];
        this.suggestionsDiv = null;
        this.input = null;
        this.chipsContainer = null;
        this.init();
    }
    
    async init() {
        await this.loadAllTags();
        this.render();
        this.attachEvents();
    }
    
    async loadAllTags() {
        try {
            this.allTags = await getTags();
        } catch (error) {
            console.error('Error loading tags:', error);
            this.allTags = [];
        }
    }
    
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with id "${this.containerId}" not found`);
            return;
        }
        
        container.innerHTML = '';
        
        const wrapper = document.createElement('div');
        wrapper.className = 'tags-input-wrapper';
        
        this.chipsContainer = document.createElement('div');
        this.chipsContainer.className = 'tags-chips';
        
        this.tags.forEach(tag => {
            const chip = this.createChip(tag);
            this.chipsContainer.appendChild(chip);
        });
        
        const input = document.createElement('input');
        input.type = 'text';
        input.id = this.inputId;
        input.className = 'tags-input';
        input.placeholder = 'Введите тег...';
        input.autocomplete = 'off';
        this.input = input;
        
        this.suggestionsDiv = document.createElement('div');
        this.suggestionsDiv.className = 'tags-suggestions';
        this.suggestionsDiv.style.display = 'none';
        
        wrapper.appendChild(this.chipsContainer);
        wrapper.appendChild(input);
        wrapper.appendChild(this.suggestionsDiv);
        container.appendChild(wrapper);
        
        this.attachInputEvents();
    }
    
    createChip(tag) {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        
        const textSpan = document.createElement('span');
        textSpan.textContent = tag;
        
        const removeSpan = document.createElement('span');
        removeSpan.className = 'tag-chip-remove';
        removeSpan.textContent = '×';
        removeSpan.setAttribute('data-tag', tag);
        
        // Критично: preventDefault + stopPropagation
        removeSpan.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.removeTag(tag);
        });
        
        chip.appendChild(textSpan);
        chip.appendChild(removeSpan);
        
        return chip;
    }
    
    attachInputEvents() {
        this.input.addEventListener('input', (e) => this.onInput(e));
        this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
        this.input.addEventListener('focus', () => {
            this.input.value = '';
            this.hideSuggestions();
        });
        
        // Закрытие подсказок при клике вне
        document.addEventListener('click', (e) => {
            if (this.suggestionsDiv && 
                !this.suggestionsDiv.contains(e.target) && 
                e.target !== this.input) {
                this.hideSuggestions();
            }
        });
    }
    
    attachEvents() {
        // Метод оставлен для совместимости
    }
    
    async onInput(e) {
        const query = e.target.value.trim().toLowerCase();
        
        if (query.length < 1) {
            this.hideSuggestions();
            return;
        }
        
        const suggestions = this.allTags
            .filter(tag => tag.name.toLowerCase().includes(query))
            .filter(tag => !this.tags.includes(tag.name))
            .slice(0, 10);
        
        this.showSuggestions(suggestions);
    }
    
    showSuggestions(suggestions) {
        if (!this.suggestionsDiv) return;
        
        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        this.suggestionsDiv.innerHTML = '';
        
        suggestions.forEach(tag => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = tag.name;
            item.setAttribute('data-tag', tag.name);
            
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.addTag(tag.name);
                this.input.value = '';
                this.hideSuggestions();
                this.input.focus();
            });
            
            this.suggestionsDiv.appendChild(item);
        });
        
        this.suggestionsDiv.style.display = 'block';
    }
    
    hideSuggestions() {
        if (this.suggestionsDiv) {
            this.suggestionsDiv.style.display = 'none';
        }
    }
    
    onKeyDown(e) {
        // Критично: полная блокировка всплытия Enter
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            
            const newTag = this.input.value.trim();
            if (newTag) {
                this.addTag(newTag);
                this.input.value = '';
                this.hideSuggestions();
            }
            return false;
        }
        
        // Backspace для удаления последнего тега
        if (e.key === 'Backspace' && this.input.value === '' && this.tags.length > 0) {
            e.preventDefault();
            this.removeTag(this.tags[this.tags.length - 1]);
        }
    }
    
    addTag(tag) {
        tag = tag.trim().toLowerCase();
        if (tag && !this.tags.includes(tag) && this.tags.length < 10 && tag.length <= 50) {
            this.tags.push(tag);
            this.render(); // Перерисовываем полностью
            if (this.input) this.input.focus();
        }
    }
    
    removeTag(tag) {
        this.tags = this.tags.filter(t => t !== tag);
        this.render();
        if (this.input) this.input.focus();
    }
    
    getTags() {
        return this.tags;
    }
    
    setTags(tags) {
        this.tags = [...tags];
        this.render();
    }
}