import asyncio
import json
import websockets

# Load your pre-generated email→integer assignments
with open("lecture_4_code/assignments.json") as f:
    ASSIGNMENTS = json.load(f)

# Calculate the actual result
actual = sum([num for _,num in ASSIGNMENTS.items()]) % 500

# Global state
active_connections = {}   # email : websocket
display_connections = set() # local display
bids = {} # list of received bids per round
asks = {} # list of received asks per round
wealth = {email:0 for email in ASSIGNMENTS.keys()} # email : wealth
inventory = {email:0 for email in ASSIGNMENTS.keys()}
TOTAL_ROUNDS = 90

round_number = 0
round_type = "buy"
prior_results = [0 for _ in range(500)]  # placeholder for auction aggregate

# Handle client connections
async def handle_connection(websocket):
    global round_type, bids, asks, wealth, inventory, active_connections
    async for msg in websocket:
        data = json.loads(msg)
        msg_type = data.get("type")
        email = data.get("email")

        # Handle integer request
        if msg_type == "integer_request":
            if email not in ASSIGNMENTS:
                wealth[email] = 0
                inventory[email] = 0
                num = None # Send out None if not in microsoft form data
            else:
                num = ASSIGNMENTS.get(email)

            print(f"{email} requested integer: {num}")
            
            # Send it
            await websocket.send(json.dumps({
                "type": "integer_response",
                "num": num
            }))
            
            active_connections[email] = websocket

        # Handle submissions
        elif msg_type == "submission":        
            level = data.get("level")
            if type(level) != int:
                continue  
            level = min(499,max(0,level))
                        
            if round_type == "buy":
                print(f"Got submission from {email}: {level}")
                bids[email] = level
                
            elif round_type == "sell":
                print(f"Got submission from {email}: {level}")
                asks[email] = level
                
        # Other message types
        else:
            print("Unknown message type:", msg_type)
            
# Regularly sends out "start of round"/"start of time unit" requests
async def game_loop():
    global round_number, round_type, prior_results, bids, asks, actual
    round_types = ["buy", "sell"]
    
    while round_number < TOTAL_ROUNDS:
        for r_t in round_types:
            round_type = r_t
            round_number += 1
            
            for time_unit in range(1,11):
                print(f"\n=== ROUND: {round_number}, TIME UNIT: {time_unit}, ROUND TYPE: ({round_type.upper()}) ===")
            
                # Broadcast
                message = json.dumps({
                    "round_number": round_number,
                    "round_type": round_type,
                    "time_unit": time_unit,
                    "prior_results": prior_results
                })
                
                await broadcast(message) # Send out the global message to all clients

                # Give players 1 second to respond
                await asyncio.sleep(1.1)

                # Processing player messages
                # Reset before updating
                prior_results = [0 for _ in range(500)]                
                
                if r_t == "buy":
                    if bids: 
                        # Update the prior results vector
                        for email, bid in bids.items():
                            prior_results[bid] += 1                     
                                    
                elif r_t == "sell":
                    if asks:
                        # Update the prior results vector
                        for email, ask in asks.items():
                            prior_results[ask] += 1
                
                # Send over stuff to display
                await broadcast_display({
                    "type": "prior_results",
                    "round_number": round_number,
                    "time_unit": time_unit,
                    "prior_results": prior_results
                })
                
            # Handle final time unit resolution
            emails = []
            if r_t == "buy":
                ppl = 0
                nums = []
                # Find the best bids
                for i in range(499,-1,-1):
                    ppl += prior_results[i]
                    if prior_results[i] > 0:
                        nums.append(i)
                    if ppl > 10:
                        break            
                
                flag = False
                for num in nums:
                    for email,bid in bids.items():
                        if bid == num:
                            emails.append(email)
                        if len(emails) == 10:
                            flag = True
                            break
                    if flag:
                        break
        
                for email in emails:
                    wealth[email] -= bids[email]
                    inventory[email] += 1
                    
        
            elif r_t == "sell":
                ppl = 0
                nums = []
                # Find the best asks
                for i in range(0,500,1):
                    ppl += prior_results[i]
                    if prior_results[i] > 0:
                        nums.append(i)
                    if ppl > 10:
                        break            
                
                flag = False
                for num in nums:
                    for email,ask in asks.items():
                        if ask == num:
                            emails.append(email)
                        if len(emails) == 10:
                            flag = True
                            break
                    if flag:
                        break
                            
                for email in emails:
                    wealth[email] += asks[email]
                    inventory[email] -= 1

            await broadcast_display({
                "type": "wealth_update",
                "round_number": round_number,
                "wealth": wealth
            })

            # Reset at the end of a round    
            bids.clear()
            asks.clear()
    
    # Resolve inventories
    for email,q in inventory.items():
        wealth[email] += q*actual
     
    await broadcast_display({
        "type": "prior_results",
        "round_number": round_number,
        "time_unit": time_unit,
        "prior_results": prior_results
    }) 
    
    await broadcast_display({
        "type": "wealth_update",
        "round_number": round_number,
        "wealth": wealth
    })

    print("✅ Game over! 90 rounds completed.")
    await broadcast({"FLAG":"GAMEOVER"}) # Send gameover to everyone's websocket
    
# Helper function to send stuff to every websocket connection
async def broadcast(msg):
    if not active_connections:
        print("No active connections.")
        return
    
    for email, ws in list(active_connections.items()):
        try:
            await ws.send(msg)
        except Exception as e:
            print(f"Lost connection to {email}: {e}")
            del active_connections[email]

async def handle_display(ws):
    display_connections.add(ws)
    try:
        async for msg in ws:
            pass
    finally:
        display_connections.remove(ws)

async def broadcast_display(data):
    if display_connections:
        msg = json.dumps(data)
        await asyncio.gather(*[ws.send(msg) for ws in display_connections])

# Main func
async def main():
    player_server = await websockets.serve(handle_connection, "0.0.0.0", 8765)
    display_server = await websockets.serve(handle_display, "0.0.0.0", 8766)
    
    print(f"Player Server running on ws://34.41.250.232:8765")
    print(f"Display Server running on ws://34.41.250.232:8766")
    
    await asyncio.sleep(300)
    
    await game_loop() 
    
asyncio.run(main())
