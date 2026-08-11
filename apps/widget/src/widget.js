/**
 * DSM-5 Psychiatry & Clinical Psychology AI Assistant - Embeddable Widget
 * Version: 1.0.0
 */

(function () {
  'use strict';

  var WebsiteAssistant = {
    config: {
      apiKey: '',
      apiEndpoint: '/api/v1',
      theme: 'dark',
      position: 'bottom-right',
      primaryColor: '#6366f1',
      welcomeMessage: "Hello! I am **DSM-5 PsychAssist AI**. I provide diagnostic criteria guidance, differential diagnosis pathways, epidemiology statistics, and psychometric tools (PHQ-9, GAD-7) based on DSM-5 standards.",
    },
    state: {
      isOpen: false,
      sessionId: 'sess_' + Math.random().toString(36).substring(2, 12),
      messages: [],
      isStreaming: false,
    },
    elements: {},

    init: function (options) {
      if (options) {
        for (var key in options) {
          if (options.hasOwnProperty(key)) {
            this.config[key] = options[key];
          }
        }
      }
      this.injectStyles();
      this.renderWidget();
      this.bindEvents();
      this.addWelcomeMessage();
    },

    injectStyles: function () {
      if (document.getElementById('wa-widget-styles')) return;
      var link = document.createElement('link');
      link.id = 'wa-widget-styles';
      link.rel = 'stylesheet';
      link.href = '/widget.css';
      document.head.appendChild(link);
    },

    renderWidget: function () {
      var container = document.createElement('div');
      container.className = 'wa-widget-container wa-position-' + this.config.position;
      container.setAttribute('data-theme', this.config.theme);

      container.innerHTML = `
        <div class="wa-chat-panel" id="wa-chat-panel">
          <div class="wa-header">
            <div class="wa-header-info">
              <div class="wa-avatar">🧠</div>
              <div>
                <div class="wa-title">DSM-5 PsychAssist AI</div>
                <div class="wa-subtitle">Psychiatry & Psychology decision support</div>
              </div>
            </div>
            <div class="wa-header-actions">
              <button class="wa-icon-btn" id="wa-theme-btn" title="Toggle Theme">☀️</button>
              <button class="wa-icon-btn" id="wa-reset-btn" title="Reset Chat">🔄</button>
              <button class="wa-icon-btn" id="wa-close-btn" title="Close Panel">✕</button>
            </div>
          </div>
          <div class="wa-body" id="wa-chat-body"></div>
          <div class="wa-suggestions" id="wa-suggestions">
            <button class="wa-sugg-chip" data-query="Major Depressive Disorder DSM-5 Criteria">Depression Criteria</button>
            <button class="wa-sugg-chip" data-query="Evaluate PHQ-9 Depression scale score">PHQ-9 Tool</button>
            <button class="wa-sugg-chip" data-query="Evaluate GAD-7 Anxiety scale score">GAD-7 Tool</button>
            <button class="wa-sugg-chip" data-query="Bipolar I vs Bipolar II differential diagnosis">Bipolar I vs II</button>
            <button class="wa-sugg-chip" data-query="Schizophrenia epidemiology and prevalence statistics">Prevalence Stats</button>
            <button class="wa-sugg-chip wa-sugg-crisis" data-query="Emergency crisis safety support hotlines">🚨 Crisis Hotline</button>
          </div>
          <div class="wa-footer">
            <div class="wa-input-wrapper">
              <textarea id="wa-chat-input" class="wa-chat-input" placeholder="Ask about DSM-5 criteria, PHQ-9, GAD-7, statistics..." rows="1"></textarea>
              <button id="wa-send-btn" class="wa-send-btn" aria-label="Send message">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="wa-teaser-bubble" id="wa-teaser-bubble">
          <span class="wa-teaser-text">Ask DSM-5 PsychAssist AI 👋</span>
          <button class="wa-teaser-close" id="wa-teaser-close" aria-label="Close bubble">✕</button>
        </div>
        <button class="wa-toggle-btn wa-pulsing" id="wa-toggle-btn" aria-label="Open AI Assistant">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        </button>
      `;

      document.body.appendChild(container);

      this.elements.container = container;
      this.elements.panel = container.querySelector('#wa-chat-panel');
      this.elements.toggleBtn = container.querySelector('#wa-toggle-btn');
      this.elements.teaserBubble = container.querySelector('#wa-teaser-bubble');
      this.elements.teaserClose = container.querySelector('#wa-teaser-close');
      this.elements.closeBtn = container.querySelector('#wa-close-btn');
      this.elements.resetBtn = container.querySelector('#wa-reset-btn');
      this.elements.themeBtn = container.querySelector('#wa-theme-btn');
      this.elements.body = container.querySelector('#wa-chat-body');
      this.elements.input = container.querySelector('#wa-chat-input');
      this.elements.sendBtn = container.querySelector('#wa-send-btn');
      this.elements.suggestions = container.querySelector('#wa-suggestions');

      this.initAttentionTimer();
    },

    initAttentionTimer: function () {
      var self = this;
      setTimeout(function () {
        if (!self.state.isOpen && self.elements.teaserBubble) {
          self.elements.teaserBubble.classList.add('wa-visible');
        }
      }, 2500);
    },

    bindEvents: function () {
      var self = this;

      if (self.elements.teaserClose) {
        self.elements.teaserClose.addEventListener('click', function (e) {
          e.stopPropagation();
          if (self.elements.teaserBubble) {
            self.elements.teaserBubble.classList.remove('wa-visible');
          }
        });
      }

      self.elements.toggleBtn.addEventListener('click', function () {
        self.togglePanel();
      });

      self.elements.closeBtn.addEventListener('click', function () {
        self.togglePanel(false);
      });

      self.elements.resetBtn.addEventListener('click', function () {
        self.resetChat();
      });

      self.elements.themeBtn.addEventListener('click', function () {
        var currentTheme = self.elements.container.getAttribute('data-theme');
        var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        self.elements.container.setAttribute('data-theme', newTheme);
      });

      self.elements.sendBtn.addEventListener('click', function () {
        self.handleSend();
      });

      if (self.elements.suggestions) {
        self.elements.suggestions.addEventListener('click', function (e) {
          var chip = e.target.closest('.wa-sugg-chip');
          if (chip && chip.dataset.query) {
            self.elements.input.value = chip.dataset.query;
            self.handleSend();
          }
        });
      }

      self.elements.input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          self.handleSend();
        }
      });
    },

    togglePanel: function (open) {
      var self = this;
      self.state.isOpen = open !== undefined ? open : !self.state.isOpen;
      if (self.state.isOpen) {
        self.elements.panel.classList.add('wa-open');
        self.elements.toggleBtn.classList.remove('wa-pulsing');
        if (self.elements.teaserBubble) {
          self.elements.teaserBubble.classList.remove('wa-visible');
        }
        self.elements.input.focus();
      } else {
        self.elements.panel.classList.remove('wa-open');
      }
    },

    addWelcomeMessage: function () {
      this.appendMessage('assistant', this.config.welcomeMessage);
    },

    resetChat: function () {
      this.elements.body.innerHTML = '';
      this.state.messages = [];
      this.state.sessionId = 'sess_' + Math.random().toString(36).substring(2, 12);
      this.addWelcomeMessage();
    },

    handleSend: function () {
      var text = this.elements.input.value.trim();
      if (!text || this.state.isStreaming) return;

      this.appendMessage('user', text);
      this.elements.input.value = '';
      this.streamResponse(text);
    },

    appendMessage: function (role, content) {
      var msgDiv = document.createElement('div');
      msgDiv.className = 'wa-message wa-msg-' + role;

      var bubble = document.createElement('div');
      bubble.className = 'wa-bubble';
      bubble.innerHTML = this.parseMarkdown(content);

      msgDiv.appendChild(bubble);
      this.elements.body.appendChild(msgDiv);
      this.scrollToBottom();

      this.state.messages.push({ role: role, content: content });
      return bubble;
    },

    fetchFallbackResponse: function (query, typingDiv) {
      var self = this;
      fetch(self.config.apiEndpoint + '/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, session_id: self.state.sessionId }),
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (typingDiv && typingDiv.parentNode) {
            self.elements.body.removeChild(typingDiv);
          }
          var b = self.appendMessage('assistant', data.response || 'No response received.');
          if (data.action) {
            self.renderActionCard(b, data.action);
          }
          self.state.isStreaming = false;
        })
        .catch(function (err) {
          if (typingDiv && typingDiv.parentNode) {
            self.elements.body.removeChild(typingDiv);
          }
          self.appendMessage('assistant', 'Sorry, I encountered an issue connecting to the DSM-5 PsychAssist AI backend.');
          self.state.isStreaming = false;
        });
    },

    streamResponse: function (query) {
      var self = this;
      self.state.isStreaming = true;

      // Show typing bubble
      var typingDiv = document.createElement('div');
      typingDiv.className = 'wa-message wa-msg-assistant';
      typingDiv.innerHTML = `
        <div class="wa-bubble wa-typing">
          <div class="wa-dot"></div><div class="wa-dot"></div><div class="wa-dot"></div>
        </div>
      `;
      self.elements.body.appendChild(typingDiv);
      self.scrollToBottom();

      var streamUrl = self.config.apiEndpoint + '/chat/stream?message=' + encodeURIComponent(query) + '&session_id=' + encodeURIComponent(self.state.sessionId);

      var responseBubble = null;
      var accumulatedText = '';

      if (window.EventSource) {
        var es = new EventSource(streamUrl);

        es.onmessage = function (event) {
          try {
            var data = JSON.parse(event.data);
            if (data.type === 'content' && data.delta) {
              if (!responseBubble) {
                if (typingDiv && typingDiv.parentNode) {
                  self.elements.body.removeChild(typingDiv);
                }
                responseBubble = self.appendMessage('assistant', '');
              }
              accumulatedText += data.delta;
              responseBubble.innerHTML = self.parseMarkdown(accumulatedText);
              if (data.action) {
                self.renderActionCard(responseBubble, data.action);
              }
              self.scrollToBottom();
            } else if (data.type === 'done') {
              es.close();
              self.state.isStreaming = false;
            }
          } catch (e) {
            console.error('SSE Error', e);
          }
        };

        es.onerror = function () {
          es.close();
          if (!responseBubble) {
            self.fetchFallbackResponse(query, typingDiv);
          } else {
            self.state.isStreaming = false;
          }
        };
      } else {
        self.fetchFallbackResponse(query, typingDiv);
      }
    },

    renderActionCard: function (containerBubble, action) {
      if (!action || !action.name) return;

      var card = document.createElement('div');
      card.className = 'wa-action-card';

      if (action.name === 'assess_phq9' || action.name === 'assess_gad7' || action.name === 'assess_pcl5') {
        var toolData = action.data || {};
        card.innerHTML = `
          <div class="wa-card-title">📝 Psychometric Assessment Result</div>
          <div class="wa-card-desc"><strong>Tool:</strong> ${toolData.tool || action.name}<br><strong>Score:</strong> ${toolData.score !== undefined ? toolData.score : 'N/A'}<br><strong>Severity:</strong> ${toolData.severity_level || toolData.interpretation || 'Evaluated'}</div>
          <div class="wa-card-rec"><strong>Recommendation:</strong> ${toolData.clinical_recommendation || toolData.recommendation || 'Clinical review recommended.'}</div>
        `;
      } else if (action.name === 'lookup_dsm5_code') {
        card.innerHTML = `
          <div class="wa-card-title">🔍 DSM-5 Diagnostic Code Lookup</div>
          <div class="wa-card-desc">${action.message || 'Diagnostic code records retrieved.'}</div>
        `;
      } else if (action.name === 'get_epidemiology_stats') {
        card.innerHTML = `
          <div class="wa-card-title">📊 Empirical Epidemiology Data</div>
          <div class="wa-card-desc">${action.message || 'Prevalence statistics retrieved.'}</div>
        `;
      } else if (action.name === 'crisis_hotline') {
        card.innerHTML = `
          <div class="wa-card-title" style="color: #fda4af;">🚨 24/7 Immediate Crisis & Safety Support</div>
          <div class="wa-card-desc" style="color: #fecdd3; margin-bottom: 10px;">Help is free, confidential, and available 24/7:</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="tel:988" style="background: #e11d48; color: white; border-radius: 6px; padding: 6px 12px; font-weight: 600; text-decoration: none; font-size: 0.82rem;" onclick="window.open('https://988lifeline.org/chat/', '_blank')">📞 Call / Text 988</a>
            <a href="https://findahelpline.com/" target="_blank" rel="noopener" style="background: rgba(255,255,255,0.15); color: white; border-radius: 6px; padding: 6px 12px; font-weight: 500; text-decoration: none; font-size: 0.82rem;">🌍 International Hotlines</a>
          </div>
        `;
      } else {
        return;
      }

      containerBubble.appendChild(card);
    },

    parseMarkdown: function (str) {
      if (!str) return '';
      var html = str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
      return html;
    },

    scrollToBottom: function () {
      if (this.elements.body) {
        this.elements.body.scrollTop = this.elements.body.scrollHeight;
      }
    },
  };

  window.WebsiteAssistant = WebsiteAssistant;
})();
