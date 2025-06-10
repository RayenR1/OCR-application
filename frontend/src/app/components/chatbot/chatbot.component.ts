import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-chatbot',
  standalone: false,
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.css',
  providers: [MessageService] 
})
export class ChatbotComponent {
  messages: any[] = [];
  userInput: string = '';
  isLoading: boolean = false;

  constructor(private messageService: MessageService) {
    this.addBotMessage('Hello! How can I assist you today?');
  }

  sendMessage() {
    if (!this.userInput.trim()) return;

    const userMessage = this.userInput;
    this.addUserMessage(userMessage);
    this.userInput = '';
    this.isLoading = true;

    setTimeout(() => {
      this.getBotResponse(userMessage);
      this.isLoading = false;
    }, 1000);
  }

  private addUserMessage(text: string) {
    this.messages.push({
      text,
      sender: 'user',
      timestamp: new Date()
    });
  }

  private addBotMessage(text: string) {
    this.messages.push({
      text,
      sender: 'bot',
      timestamp: new Date()
    });
  }

  private getBotResponse(userInput: string) {
    const responses = [
      "I understand you're asking about: " + userInput,
      "Here's what I found regarding: " + userInput,
      "I'm looking into your question about: " + userInput,
      "Could you clarify your question about: " + userInput + "?"
    ];
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    this.addBotMessage(randomResponse);
  }

  clearChat() {
    this.messages = [];
    this.addBotMessage('Conversation cleared. How can I help you?');
    this.messageService.add({
      severity: 'info',
      summary: 'Cleared',
      detail: 'Chat history cleared',
      life: 3000
    });
  }
}

