import os
import re

import requests
import yaml
from colorama import Fore, Style
from git.repo import Repo

from autogpt.logs import logger

# Use readline if available (for clean_input)
try:
    import readline
except ImportError:
    pass

from autogpt.config import Config


def clean_input(prompt: str = "", talk=False):
    try:
        cfg = Config()
        if cfg.chat_messages_enabled:
            for plugin in cfg.plugins:
                if not hasattr(plugin, "can_handle_user_input"):
                    continue
                if not plugin.can_handle_user_input(user_input=prompt):
                    continue
                plugin_response = plugin.user_input(user_input=prompt)
                if not plugin_response:
                    continue
                if plugin_response.lower() in [
                    "yes",
                    "yeah",
                    "y",
                    "ok",
                    "okay",
                    "sure",
                    "alright",
                ]:
                    return cfg.authorise_key
                elif plugin_response.lower() in [
                    "no",
                    "nope",
                    "n",
                    "negative",
                ]:
                    return cfg.exit_key
                return plugin_response

        # ask for input, default when just pressing Enter is y
        #请求输入，当按下回车键时默认是y
        logger.info("通过键盘询问用户...")
        answer = input(prompt)
        return answer
    except KeyboardInterrupt:
        logger.info("您中断了AutoGPT")
        logger.info("退出中...")
        exit(0)


def validate_yaml_file(file: str):
    try:
        with open(file, encoding="utf-8") as fp:
            yaml.load(fp.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        return (False, f"文件 {Fore.CYAN}`{file}`{Fore.RESET} 没有找到")
    except yaml.YAMLError as e:
        return (
            False,
            f"在尝试读取您的AI设置文件时出现问题：{e}",
        )

    return (True, f"成功验证了 {Fore.CYAN}{file}{Fore.RESET}!")


def readable_file_size(size, decimal_places=2):
    """Converts the given size in bytes to a readable format.
    Args:
        size: Size in bytes
        decimal_places (int): Number of decimal places to display
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_bulletin_from_web():
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/Significant-Gravitas/Auto-GPT/master/BULLETIN.md"
        )
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        pass

    return ""


def get_current_git_branch() -> str:
    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch
        return branch.name
    except:
        return ""


def get_latest_bulletin() -> tuple[str, bool]:
    exists = os.path.exists("CURRENT_BULLETIN.md")
    current_bulletin = ""
    if exists:
        current_bulletin = open("CURRENT_BULLETIN.md", "r", encoding="utf-8").read()
    new_bulletin = get_bulletin_from_web()
    is_new_news = new_bulletin != "" and new_bulletin != current_bulletin

    news_header = Fore.YELLOW + "Welcome to Auto-GPT!\n"
    if new_bulletin or current_bulletin:
        news_header += (
            "Below you'll find the latest Auto-GPT News and updates regarding features!\n"
            "If you don't wish to see this message, you "
            "can run Auto-GPT with the *--skip-news* flag.\n"
        )

    if new_bulletin and is_new_news:
        open("CURRENT_BULLETIN.md", "w", encoding="utf-8").write(new_bulletin)
        current_bulletin = f"{Fore.RED}::NEW BULLETIN::{Fore.RESET}\n\n{new_bulletin}"

    return f"{news_header}\n{current_bulletin}", is_new_news


def markdown_to_ansi_style(markdown: str):
    ansi_lines: list[str] = []
    for line in markdown.split("\n"):
        line_style = ""

        if line.startswith("# "):
            line_style += Style.BRIGHT
        else:
            line = re.sub(
                r"(?<!\*)\*(\*?[^*]+\*?)\*(?!\*)",
                rf"{Style.BRIGHT}\1{Style.NORMAL}",
                line,
            )

        if re.match(r"^#+ ", line) is not None:
            line_style += Fore.CYAN
            line = re.sub(r"^#+ ", "", line)

        ansi_lines.append(f"{line_style}{line}{Style.RESET_ALL}")
    return "\n".join(ansi_lines)
