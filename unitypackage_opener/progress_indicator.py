"""
Progress indication utilities for extraction process.
"""
import ctypes
import os
import sys
from contextlib import contextmanager
from typing import Generator


class WindowsCursor:
    """Windows system cursor management"""
    
    # Windows cursor constants
    IDC_ARROW = 32512
    IDC_WAIT = 32514
    IDC_APPSTARTING = 32650  # Arrow with small hourglass
    
    @staticmethod
    def set_cursor(cursor_id: int) -> None:
        """Set system cursor"""
        try:
            if sys.platform == "win32":
                cursor = ctypes.windll.user32.LoadCursorW(None, cursor_id)
                ctypes.windll.user32.SetCursor(cursor)
        except Exception:
            pass  # Fail silently if cursor change fails
    
    @staticmethod
    def set_wait_cursor() -> None:
        """Show wait/busy cursor"""
        WindowsCursor.set_cursor(WindowsCursor.IDC_WAIT)
    
    @staticmethod
    def set_working_cursor() -> None:
        """Show working cursor (arrow + hourglass)"""
        WindowsCursor.set_cursor(WindowsCursor.IDC_APPSTARTING)
    
    @staticmethod
    def restore_cursor() -> None:
        """Restore normal cursor"""
        WindowsCursor.set_cursor(WindowsCursor.IDC_ARROW)


@contextmanager
def extraction_progress_indicator(
    show_cursor: bool = True,
    create_temp_file: bool = True,
    output_dir: str = None
) -> Generator[None, None, None]:
    """
    Context manager for showing extraction progress.
    
    Args:
        show_cursor: Whether to change system cursor
        create_temp_file: Whether to create temporary indicator file
        output_dir: Output directory for temp file
    """
    temp_file_path = None
    
    try:
        # Set cursor to indicate work in progress
        if show_cursor:
            WindowsCursor.set_working_cursor()
        
        # Create temporary indicator file
        if create_temp_file and output_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
                temp_file_path = os.path.join(output_dir, "⏳_extracting.tmp")
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write("Unity package extraction in progress...\n")
                    f.write("Please do not modify files in this directory.\n")
            except Exception:
                temp_file_path = None
        
        yield
        
    finally:
        # Restore cursor
        if show_cursor:
            WindowsCursor.restore_cursor()
        
        # Remove temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


def try_show_toast_notification(title: str, message: str) -> bool:
    """
    Attempt to show Windows toast notification.
    Returns True if successful, False otherwise.
    """
    try:
        # Try win11toast first (more modern)
        import win11toast
        win11toast.notify(
            title=title,
            body=message,
            duration="short",
            app_id="UnityPackageOpener"
        )
        return True
    except ImportError:
        pass
    
    try:
        # Fallback to plyer
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=3
        )
        return True
    except ImportError:
        pass
    
    return False