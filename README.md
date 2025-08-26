# MTG Archetype Predictor

A web-based tool for **Magic: The Gathering** enthusiasts and data annotators. This application helps you classify MTG cards into archetypes and provides AI-powered suggestions for probable archetypes based on card text.
This is a fan project with the aim of learning.

Built with **Flask**, **PostgreSQL**, and a simple **neural network model**, it offers a comfortable interface for annotation and deck archetype analysis.

---

## 🔮 Features

### **1. Card Search**
Easily find cards using multiple search criteria:
- Partial name match
- Partial text match
- Card color
- Card type
- Converted Mana Cost (CMC)

### **2. Dashboard**
Stay on top of your annotation progress with a clean dashboard:
- Track which cards have been annotated
- View the number of cards annotated per archetype

### **3. Annotation Tool**
- View a basic display of the selected card
- Submit your annotation for its archetype
- Neural network suggestions: The app provides **probable archetype hints** using a Bag-of-Words model on card text

---

## 🧠 How It Works

1. **Data Storage**
   - All card data and annotations are stored in a **PostgreSQL** relational database.

2. **Neural Network Model**
   - Uses a **Bag-of-Words** approach to process card text.
   - Provides **archetype predictions** as hints to assist with manual annotation.

3. **Flask Web App**
   - Handles user interaction, search functionality, and annotation workflow.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Database:** PostgreSQL
- **Model:** Neural Network (Bag-of-Words feature extraction for the card text and one-hot encoding for the other attributes. ) 
- **Frontend:** HTML/CSS, Bootstrap

---

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- PostgreSQL 12+
- Torch ???

Todo: setup
