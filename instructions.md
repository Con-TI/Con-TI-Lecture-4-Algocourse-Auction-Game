Setup: Go to google cloud (or AWS), set up a VM, add tcp port permissions to firewall rules that lets 0.0.0.0/0 ip connect to tp 8765 and 8766. After this create a python file and copy paste game.py into it (you may need to modify the file path strings inside the game.py file). Add in assignments.json which maps emails to assigned integers (I retrieved this via a microsoft forms result csv but you can modify how this is done). 

Note that you will need to swap out the websockets ip address that it used since the one currently in the file was used only for the lecture (and it has expired).

1. open display.html in browser
2. run generate_nums.py
3. Update the assignments.json file on the VM
4. run game.py on the VM
5. Check that the lecture_4 file can run without error (the last cell should be stuck in a loop).