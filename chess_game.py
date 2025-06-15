import chess
import chess.svg
import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Enhanced Rate limiting for API calls
class RateLimiter:
    def __init__(self, max_calls_per_minute=6, max_calls_per_day=800):  # Very conservative limits
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_day = max_calls_per_day
        self.calls_per_minute = []
        self.calls_per_day = []
        self.last_reset_time = datetime.now()
    
    def wait_if_needed(self):
        now = datetime.now()
        current_time = time.time()
        
        # Reset daily counter if a new day has started
        if now.date() > self.last_reset_time.date():
            self.calls_per_day = []
            self.last_reset_time = now
            print(f"Daily quota reset at {now.strftime('%H:%M:%S')}")
        
        # Remove calls older than 1 minute
        minute_ago = current_time - 60
        self.calls_per_minute = [call_time for call_time in self.calls_per_minute if call_time > minute_ago]
        
        # Remove calls older than 1 day
        day_ago = current_time - (24 * 60 * 60)
        self.calls_per_day = [call_time for call_time in self.calls_per_day if call_time > day_ago]
        
        # Check daily limit first
        if len(self.calls_per_day) >= self.max_calls_per_day:
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_seconds = (tomorrow - now).total_seconds()
            print(f"Daily quota of {self.max_calls_per_day} calls exceeded.")
            print(f"Waiting until tomorrow ({tomorrow.strftime('%Y-%m-%d %H:%M:%S')}) - {wait_seconds/3600:.1f} hours")
            time.sleep(wait_seconds)
            self.calls_per_minute = []
            self.calls_per_day = []
            return
        
        # Check per-minute limit
        if len(self.calls_per_minute) >= self.max_calls_per_minute:
            oldest_call = min(self.calls_per_minute)
            wait_time = 60 - (current_time - oldest_call) + 5  # Add 5 seconds buffer
            
            if wait_time > 0:
                print(f"Rate limit reached ({len(self.calls_per_minute)}/{self.max_calls_per_minute} calls per minute).")
                print(f"Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                current_time = time.time()
                minute_ago = current_time - 60
                self.calls_per_minute = [call_time for call_time in self.calls_per_minute if call_time > minute_ago]
        
        # Record this call
        self.calls_per_minute.append(current_time)
        self.calls_per_day.append(current_time)
        
        # Show usage every few calls
        if len(self.calls_per_minute) % 2 == 1:
            print(f"📊 API usage: {len(self.calls_per_minute)}/{self.max_calls_per_minute} this minute, {len(self.calls_per_day)}/{self.max_calls_per_day} today")

# Global rate limiter
rate_limiter = RateLimiter()

# Global game state
class GameState:
    def __init__(self):
        self.should_terminate = False
        self.termination_reason = ""
        self.move_count = 0
        self.consecutive_errors = 0
        
    def terminate_game(self, reason):
        self.should_terminate = True
        self.termination_reason = reason
        print(f"🛑 Game terminating: {reason}")

game_state = GameState()

class DirectGeminiChessPlayer:
    """Chess player that calls Gemini API directly, bypassing AutoGen completely"""
    
    def __init__(self, color: str, api_key: str):
        self.color = color
        self.name = f"Player_{color.title()}"
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        opponent_color = "black" if color == "white" else "white"
        self.system_prompt = f"""You are an expert chess player playing as {color} pieces.
Your opponent plays as {opponent_color} pieces.

CRITICAL INSTRUCTIONS:
1. You must respond with ONLY a valid UCI move notation (e.g., e2e4, g1f3, e1g1, a7a8q)
2. Do NOT include any explanations, comments, or extra text
3. Do NOT use algebraic notation (like Nf3) - use UCI format only
4. Your response must be exactly one move like: e2e4
5. Make sure your move is legal in the current position

You are a strong chess player who thinks strategically about piece development, control of center, king safety, and tactical opportunities."""

    def get_move(self, board: chess.Board) -> Optional[str]:
        """Get a chess move from Gemini API directly"""
        try:
            rate_limiter.wait_if_needed()
            
            # Get current position info
            legal_moves = list(board.legal_moves)
            legal_moves_str = ", ".join([str(move) for move in legal_moves[:15]])
            
            # Create the prompt
            prompt = f"""{self.system_prompt}

Current chess position (FEN): {board.fen()}

Visual board:
{board}

It's {self.color}'s turn. Legal moves: {legal_moves_str}

Your move (UCI format only):"""

            # Prepare API request
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 20,
                    "candidateCount": 1
                }
            }
            
            print(f"🤔 {self.name} is thinking...")
            
            # Make API call
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ API error for {self.name}: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            # Extract move from response
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                move_str = content.strip().split()[0]  # Take first word only
                
                print(f"💭 {self.name} suggests: {move_str}")
                return move_str
            
            print(f"❌ No valid response from {self.name}")
            return None
            
        except requests.exceptions.Timeout:
            print(f"⏱️ API timeout for {self.name}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ API request error for {self.name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error getting move from {self.name}: {e}")
            return None

class ChessGame:
    """Simple chess game controller using direct API calls"""
    
    def __init__(self, api_key: str):
        self.board = chess.Board()
        self.move_history = []
        
        # Create players with direct API access
        self.white_player = DirectGeminiChessPlayer("white", api_key)
        self.black_player = DirectGeminiChessPlayer("black", api_key)
        
    def _validate_and_make_move(self, uci_move_str: str) -> bool:
        """Validate and execute a move on the board"""
        try:
            # Clean the move string
            uci_move_str = uci_move_str.strip().lower()
            
            # Parse UCI move
            move = chess.Move.from_uci(uci_move_str)
            
            # Check if move is legal
            if move not in self.board.legal_moves:
                legal_moves = [str(m) for m in list(self.board.legal_moves)[:8]]
                print(f"❌ Illegal move: {uci_move_str}")
                print(f"   Legal moves: {', '.join(legal_moves)}...")
                return False
            
            # Execute the move
            self.board.push(move)
            game_state.move_count += 1
            self.move_history.append(uci_move_str)
            
            print(f"✅ Move {game_state.move_count}: {uci_move_str}")
            
            # Save board visualization
            self._save_board_svg()
            
            # Reset consecutive errors on successful move
            game_state.consecutive_errors = 0
            
            return True
            
        except ValueError as e:
            print(f"❌ Invalid UCI move format: {uci_move_str} - {e}")
            return False
        except Exception as e:
            print(f"❌ Error making move: {e}")
            return False
    
    def _save_board_svg(self):
        """Save current board position as SVG"""
        try:
            moves_dir = 'moves'
            if not os.path.exists(moves_dir):
                os.makedirs(moves_dir)
            svg_filename = os.path.join(moves_dir, f'move_{game_state.move_count}.svg')
            svg_output = chess.svg.board(self.board)
            with open(svg_filename, 'w') as file:
                file.write(svg_output)
            print(f"💾 Board saved: {svg_filename}")
        except Exception as e:
            print(f"⚠️ Could not save SVG: {e}")
    
    def _check_game_over(self) -> bool:
        """Check if game has ended"""
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn else "White"
            game_state.terminate_game(f"CHECKMATE! {winner} wins!")
            return True
        elif self.board.is_stalemate():
            game_state.terminate_game("STALEMATE! Draw.")
            return True
        elif self.board.is_insufficient_material():
            game_state.terminate_game("DRAW! Insufficient material.")
            return True
        elif self.board.is_fivefold_repetition():
            game_state.terminate_game("DRAW! Fivefold repetition.")
            return True
        elif self.board.is_seventyfive_moves():
            game_state.terminate_game("DRAW! Seventy-five move rule.")
            return True
        
        return False
    
    def _display_board(self):
        """Display current board state"""
        print(f"\nCurrent position after move {game_state.move_count}:")
        print(f"{'White' if self.board.turn else 'Black'} to move")
        print(self.board)
        print("-" * 60)
    
    def play_game(self, max_moves: int = 100):
        """Main game loop"""
        print("🚀 Starting Direct API Chess Game!")
        print("🔧 Completely bypassing AutoGen - using direct Gemini API calls")
        print("Initial position:")
        print(self.board)
        print("-" * 60)
        
        start_time = datetime.now()
        
        try:
            while not game_state.should_terminate and game_state.move_count < max_moves:
                # Determine current player
                current_player = self.white_player if self.board.turn else self.black_player
                
                # Get move from current player
                move_str = current_player.get_move(self.board)
                
                if move_str is None:
                    game_state.consecutive_errors += 1
                    print(f"❌ {current_player.name} failed to provide a move (errors: {game_state.consecutive_errors})")
                    
                    if game_state.consecutive_errors >= 3:
                        game_state.terminate_game(f"Too many consecutive errors from {current_player.name}")
                        break
                    
                    # Wait and try again
                    time.sleep(3)
                    continue
                
                # Validate and make the move
                if not self._validate_and_make_move(move_str):
                    game_state.consecutive_errors += 1
                    print(f"❌ Invalid move from {current_player.name}: {move_str} (errors: {game_state.consecutive_errors})")
                    
                    if game_state.consecutive_errors >= 5:
                        game_state.terminate_game("Too many invalid moves")
                        break
                    
                    time.sleep(2)
                    continue
                
                # Display board
                self._display_board()
                
                # Check if game is over
                if self._check_game_over():
                    break
                
                # Delay between moves
                time.sleep(3)
                
            # Check if we hit move limit
            if game_state.move_count >= max_moves:
                game_state.terminate_game(f"Maximum moves ({max_moves}) reached")
                
        except KeyboardInterrupt:
            print("\n🛑 Game stopped by user")
            game_state.terminate_game("User interrupted")
        except Exception as e:
            print(f"❌ Game error: {e}")
            game_state.terminate_game(f"Error: {e}")
        
        # Print final statistics
        self._print_final_stats(start_time)
    
    def _print_final_stats(self, start_time):
        """Print game statistics"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🏁 GAME OVER")
        print(f"📊 Final Statistics:")
        print(f"   • Total moves: {game_state.move_count}")
        print(f"   • Duration: {duration}")
        print(f"   • Reason: {game_state.termination_reason}")
        print(f"   • Move history: {' '.join(self.move_history)}")
        
        if self.board.is_game_over():
            result = self.board.result()
            if result == "1-0":
                print(f"🏆 Winner: White")
            elif result == "0-1":
                print(f"🏆 Winner: Black")
            else:
                print(f"🤝 Result: Draw ({result})")
        
        print(f"\nFinal position:")
        print(self.board)

def main():
    # Check if Google API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Please set the GOOGLE_API_KEY in your .env file")
        print("Create a .env file in your project directory with:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print("You can get your API key from: https://makersuite.google.com/app/apikey")
        return

    print("🚀 Starting DIRECT API Chess Game")
    print("🔧 NO AutoGen - Pure Gemini API calls")
    print("📊 Ultra-conservative rate limiting: 6 calls/minute")
    print("🎮 Press Ctrl+C anytime to stop")
    print("-" * 60)

    # Create and start the game
    game = ChessGame(api_key)
    game.play_game(max_moves=100)

if __name__ == "__main__":
    main()