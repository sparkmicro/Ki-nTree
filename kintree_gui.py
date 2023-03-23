import sys
from kintree.kintree_gui import main

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(view='browser')
        sys.exit()
    main(view='flet_app')
