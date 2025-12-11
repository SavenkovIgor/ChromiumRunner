import FreeSimpleGUI as sg


def main():
    # Create a simple window with a "Hello World" label
    layout = [[sg.Text("Hello World")]]
    
    window = sg.Window("Hello World App", layout)
    
    # Event loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
    
    window.close()


if __name__ == "__main__":
    main()
