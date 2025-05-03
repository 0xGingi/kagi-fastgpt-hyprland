# Kagi FastGPT Popup for Hyprland

A simple popup chat interface using the Kagi FastGPT API, designed to be toggled with a keybind in Hyprland.

## Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/0xgingi/kagi-fastgpt-hyprland
2.  **Install dependencies:**
    ```bash
    sudo pacman -S --needed jq pyside6 python-requests python-dotenv
    ```
3.  **Set API Token:**
    Create a `.env` file with the following content:
    ```dotenv
    KAGI_API_TOKEN=your_kagi_api_token_here
    ```

4.  **Configure Toggle Script:**
    Edit `kagi-fastgpt-hyprland/toggle_chat.sh` and set `PYTHON_SCRIPT_PATH` to the path of `kagi-fastgpt-hyprland/main.py`. For example:
    ```bash
    PYTHON_SCRIPT_PATH="/home/$USER/kagi-fastgpt-hyprland/main.py"
    ```
    Make the script executable:
    ```bash
    chmod +x toggle_chat.sh
    ```

5.  **Configure Hyprland:**
    Add the following to your `hyprland.conf`, changing your preferred bind and path to toggle_chat.sh:

    ```hyprland
    bind = $mainMod, X, exec, /path/to/your/kagi-fastgpt-hyprland/toggle_chat.sh

    windowrulev2 = float, class:^(python3)$,title:^(Kagi FastGPT)$
    windowrulev2 = size 60% 70%, class:^(python3)$,title:^(Kagi FastGPT)$
    windowrulev2 = center, class:^(python3)$,title:^(Kagi FastGPT)$
    ```
