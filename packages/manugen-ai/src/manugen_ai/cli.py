from pathlib import Path
from cyclopts import App

app = App()

@app.default
def manugen(content_dir: Path):
    print("* Manugen AI CLI *")
    print(f"Content directory: {content_dir.resolve()}")

    print("...this will eventually do something useful...")

if __name__ == '__main__':
    app()
