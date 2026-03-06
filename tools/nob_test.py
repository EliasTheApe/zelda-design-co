#!/usr/bin/env python3
"""NOB catch-all diagnostic — catches scroll, keys, buttons, everything"""
import tkinter as tk

root = tk.Tk()
root.title("NOB Test — move cursor HERE then turn NOB")
root.geometry("600x500+100+100")
root.configure(bg="#1a1714")

# Big visible target — cursor must be over this window
tk.Label(root, text="◀  HOVER CURSOR HERE WHILE TURNING NOB  ▶",
         font=("Courier", 11, "bold"), bg="#2a2218", fg="#b89a6e",
         pady=12).pack(fill=tk.X)

log = tk.Text(root, font=("Courier", 10), bg="#111", fg="#b89a6e",
              state=tk.NORMAL)
log.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

tk.Button(root, text="Clear", bg="#2a2520", fg="#b89a6e", relief=tk.FLAT,
          command=lambda: log.delete("1.0", tk.END)).pack(pady=2)

count = [0]

def rec(label, extra=""):
    count[0] += 1
    msg = f"#{count[0]:04d}  {label}  {extra}\n"
    log.insert(tk.END, msg)
    log.see(tk.END)
    print(msg, end="", flush=True)

# Scroll / wheel
root.bind_all("<MouseWheel>",
    lambda e: rec("MouseWheel", f"delta={e.delta} num={e.num} state={e.state}"))
root.bind_all("<Button-4>",
    lambda e: rec("Button-4  (scroll up)", f"x={e.x} y={e.y}"))
root.bind_all("<Button-5>",
    lambda e: rec("Button-5  (scroll dn)", f"x={e.x} y={e.y}"))

# All other mouse buttons
for btn in (1,2,3,6,7,8,9):
    root.bind_all(f"<Button-{btn}>",
        lambda e, b=btn: rec(f"Button-{b}", f"x={e.x} y={e.y}"))
    root.bind_all(f"<ButtonRelease-{btn}>",
        lambda e, b=btn: rec(f"Release-{b}"))

# Keys — catches if NOB sends keypresses
root.bind_all("<Key>",
    lambda e: rec("Key", f"sym={e.keysym!r} char={e.char!r} code={e.keycode}"))

# Motion
root.bind_all("<Motion>",
    lambda e: rec("Motion", f"dx={e.x} dy={e.y} state={e.state}"))

root.mainloop()
