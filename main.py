from pyAsciiEngine import ConsoleScreen, Colors, Styles, TextStyle, Anchors, Symbol
import pyAsciiEngine
print(pyAsciiEngine)

def main():
    sc = ConsoleScreen()
    st = TextStyle(Colors.CYAN, Colors.BLACK, Styles.BOLD)

    while True:
        x, y = sc.get_sizes()
        sc.set_str(0,0,"hello")
        sc.set_str(x // 2, y-1, f"Sizes: {x} {y}", anchor=Anchors.CENTER_X_ANCHOR, style=st)
        sc.draw_rectangle(5, 5, 5+4, 5+4, Symbol("*"), isFill=False)

        key = sc.get_key()
        sc.update()
        if key == "q":
            break

if __name__ == '__main__':
    main()