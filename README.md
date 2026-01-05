## Prerequisites

- `uv` must be installed. You can find installation instructions [here](https://docs.astral.sh/uv/getting-started/installation/).

## Steps to run

1.  Clone the repository and navigate to the project directory:
    ```bash
    git clone https://github.com/mysticshirou/subwaysurfers_irl.git
    cd subwaysurfers_irl
    ```
2.  Install the dependencies using `uv`:
    ```bash
    uv sync
    ```
3.  Run the flask application:
    ```bash
    uv run flask/app.py
    ```
4. Open [127.0.0.1:5000](127.0.0.1:5000) on Google Chrome (Does not work on Firefox)

## How to play the game
When the webpage loads, there would be the webcam on the left, and the Subway Surfers game on the right.
### Webcam
You will notice gridlines on the webcam image. These gridlines are different controls of the game. The grids follow this pattern:
```python
           Left   Centre   Right
Jump    (-1,  1) (0,  1) (1,  1)
Neutral (-1,  0) (0,  0) (1,  0)
Roll    (-1, -1) (0, -1) (1, -1)

      X  Y
    (-1, 1)
```

For example, if a player goes on the top left box of the grid, they will **jump + move left**.
