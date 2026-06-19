import tkinter as tk

root = tk.Tk()
root.title("fan speed")
root.geometry("300x300")

speed = tk.IntVar()

tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, variable=speed).pack(pady=20)
label = tk.Label(root, text="0%")
label.pack()

fan = tk.Label(root, text="|", font=("Courier", 48))
fan.pack(pady=30)

frames = ["|", "/", "-", "\\"]
i = 0

def update():
    global i
    s = speed.get()
    label.config(text=f"{s}%")
    if s > 0:
        i += 1
        fan.config(text=frames[i % 4])
    root.after(200 - s, update)

update()
root.mainloop()
