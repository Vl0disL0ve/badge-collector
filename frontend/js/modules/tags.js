class TagsAutocomplete {
    constructor(inputId, containerId, existingTags = []) {
        this.inputId = inputId;
        this.containerId = containerId;
        this.tags = [...existingTags];
        this.allTags = [];
        this.suggestionsDiv = null;
        this.input = null;
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
        
        const chipsContainer = document.createElement('div');
        chipsContainer.className = 'tags-chips';
        
        this.tags.forEach(tag => {
            const chip = this.createChip(tag);
            chipsContainer.appendChild(chip);
        });
        
        const input = document.createElement('input');
        input.type = 'text';
        input.id = this.inputId;
        input.className = 'tags-input';
        input.placeholder = 'Введите тег...';
        input.autocomplete = 'off';
        
        this.suggestionsDiv = document.createElement('div');
        this.suggestionsDiv.className = 'tags-suggestions';
        this.suggestionsDiv.style.display = 'none';
        
        wrapper.appendChild(chipsContainer);
        wrapper.appendChild(input);
        wrapper.appendChild(this.suggestionsDiv);
        container.appendChild(wrapper);
        
        this.input = input;
        this.chipsContainer = chipsContainer;
    }
    
    createChip(tag) {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.innerHTML = `${escapeHtml(tag)} <span class="tag-chip-remove" data-tag="${escapeHtml(tag)}">×</span>`;
        
        const removeBtn = chip.querySelector('.tag-chip-remove');
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeTag(tag);
        });
        
        return chip;
    }
    
    attachEvents() {
        if (!this.input) return;
        
        this.input.addEventListener('input', (e) => this.onInput(e));
        this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
        this.input.addEventListener('focus', () => this.input.value = '');
        document.addEventListener('click', (e) => {
            if (this.suggestionsDiv && !this.suggestionsDiv.contains(e.target) && e.target !== this.input) {
                this.hideSuggestions();
            }
        });
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
        
        this.suggestionsDiv.innerHTML = suggestions.map(tag => `
            <div class="suggestion-item" data-tag="${escapeHtml(tag.name)}">
                ${escapeHtml(tag.name)}
            </div>
        `).join('');
        
        this.suggestionsDiv.style.display = 'block';
        
        this.suggestionsDiv.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const tag = item.dataset.tag;
                this.addTag(tag);
                this.input.value = '';
                this.hideSuggestions();
                this.input.focus();
            });
        });
    }
    
    hideSuggestions() {
        if (this.suggestionsDiv) {
            this.suggestionsDiv.style.display = 'none';
        }
    }
    
    onKeyDown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const newTag = this.input.value.trim();
            if (newTag) {
                this.addTag(newTag);
                this.input.value = '';
                this.hideSuggestions();
            }
        } else if (e.key === 'Backspace' && this.input.value === '' && this.tags.length > 0) {
            this.removeTag(this.tags[this.tags.length - 1]);
        }
    }
    
    addTag(tag) {
        tag = tag.trim().toLowerCase();
        if (tag && !this.tags.includes(tag) && this.tags.length < 10) {
            this.tags.push(tag);
            this.render();
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