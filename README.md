# AI Chess Game - Direct Gemini API Implementation

A Python chess game where two AI players powered by Google's Gemini API play against each other. This implementation bypasses AutoGen and uses direct API calls for clean, efficient gameplay.

## 🎯 Features

- **Direct API Integration**: Uses Google Gemini 1.5 Flash API directly without AutoGen framework
- **AI vs AI Gameplay**: Two Gemini-powered players compete in full chess games
- **Smart Rate Limiting**: Conservative API usage with 6 calls/minute and 800 calls/day limits
- **Visual Board Export**: Saves each move as SVG files for game analysis
- **Comprehensive Game Logic**: Full chess rules implementation with checkmate, stalemate, and draw detection
- **Error Handling**: Robust error recovery and move validation
- **Real-time Statistics**: Live game stats and final game summary

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Google API Key (Gemini API access)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/naakaarafr/AI-Chess-Game.git
   cd AI-Chess-Game
   ```

2. **Install dependencies**
   ```bash
   pip install chess requests python-dotenv
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```
   
   Get your API key from: [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Run the game**
   ```bash
   python chess_game.py
   ```

## 🎮 How It Works

### Game Flow
1. **Initialization**: Creates two AI players (White and Black) with direct Gemini API access
2. **Move Generation**: Each player analyzes the current position and generates UCI format moves
3. **Move Validation**: Validates moves against chess rules before execution
4. **Board Updates**: Updates position and saves visual representation
5. **Game End Detection**: Checks for checkmate, stalemate, and other draw conditions

### AI Player Behavior
- Uses strategic chess thinking focused on piece development, center control, and king safety
- Responds only with valid UCI notation moves (e.g., `e2e4`, `g1f3`)
- Analyzes current position using FEN notation and legal move lists

## 📁 Project Structure

```
AI-Chess-Game/
├── chess_game.py          # Main game implementation
├── .env                   # Environment variables (create this)
├── moves/                 # Generated SVG files (auto-created)
│   ├── move_1.svg
│   ├── move_2.svg
│   └── ...
└── README.md
```

## ⚙️ Configuration

### Rate Limiting
The game includes conservative rate limiting to respect API quotas:
- **Per minute**: 6 API calls maximum
- **Per day**: 800 API calls maximum
- **Auto-reset**: Daily quota resets at midnight

### Game Settings
You can modify these parameters in the `main()` function:
- `max_moves`: Maximum moves per game (default: 100)
- `temperature`: AI creativity level (default: 0.3)
- `maxOutputTokens`: Response length limit (default: 20)

### API Configuration
Adjust rate limits in the `RateLimiter` class:
```python
rate_limiter = RateLimiter(
    max_calls_per_minute=6,    # Adjust as needed
    max_calls_per_day=800      # Adjust based on your quota
)
```

## 🎯 Game Output

### Console Output
- Real-time move notifications
- Board position after each move
- API usage statistics
- Error messages and recovery attempts
- Final game statistics

### Generated Files
- **SVG Files**: Visual board representation saved in `moves/` directory
- **File naming**: `move_1.svg`, `move_2.svg`, etc.

### Example Game Summary
```
🏁 GAME OVER
📊 Final Statistics:
   • Total moves: 34
   • Duration: 0:12:45
   • Reason: CHECKMATE! White wins!
   • Move history: e2e4 e7e5 g1f3 b8c6 ...
🏆 Winner: White
```

## 🔧 Troubleshooting

### Common Issues

**API Key Error**
```
Error: Please set the GOOGLE_API_KEY in your .env file
```
- Ensure `.env` file exists with valid API key
- Check API key has Gemini API access enabled

**Rate Limit Exceeded**
```
Rate limit reached (6/6 calls per minute). Waiting 65.1 seconds...
```
- This is normal behavior - the game will automatically wait
- Consider reducing call frequency if needed

**Invalid Move Errors**
```
❌ Illegal move: e2e5
```
- AI occasionally generates invalid moves
- Game automatically retries with error recovery
- Too many consecutive errors will terminate the game

### Performance Tips

1. **Reduce API calls**: Increase thinking time between moves
2. **Monitor usage**: Watch the built-in API usage statistics
3. **Adjust limits**: Modify rate limiter settings based on your quota

## 🔍 Advanced Usage

### Custom Player Configuration
You can modify the system prompt in `DirectGeminiChessPlayer` to change playing style:
```python
self.system_prompt = f"""You are an aggressive chess player playing as {color} pieces.
Focus on attacking moves and tactical combinations..."""
```

### Game Analysis
Use the generated SVG files to:
- Analyze game progression
- Create animated game replays
- Study AI decision-making patterns

### Integration Options
The modular design allows easy integration with:
- Chess engines for analysis
- Tournament management systems
- Web interfaces for online play

## 📊 API Usage Monitoring

The game provides real-time API usage statistics:
```
📊 API usage: 3/6 this minute, 45/800 today
```

Daily quotas reset automatically at midnight with notification:
```
Daily quota reset at 00:00:01
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Opening book integration
- Endgame tablebase support
- Tournament mode
- Web interface
- Analysis engine integration

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with the [python-chess](https://python-chess.readthedocs.io/) library
- Powered by Google's Gemini 1.5 Flash API
- Created by [@naakaarafr](https://github.com/naakaarafr)

---

**Ready to watch AI play chess?** Run `python chess_game.py` and enjoy the match! 🏆
