import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QHBoxLayout, QTabWidget,
    QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, pyqtSignal


# --- 1. Custom Widget for Each Browser Tab ---
class BrowserTab(QWidget):
    # Custom signals to communicate URL and title changes from this tab to the main window
    url_updated_signal = pyqtSignal(QUrl)
    title_updated_signal = pyqtSignal(str)

    def __init__(self, main_browser_window, parent=None):
        super().__init__(parent)
        self.main_browser_window = main_browser_window # Reference to the main window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # No margins for the web view within the tab

        # Web Engine View - This is the main content area for the tab
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view) # Web view fills the tab's content area

        # Define path for local default page (welcome.html)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_page_path = os.path.join(script_dir, 'welcome.html')

        # Connect signals for internal updates and communication with main window
        self.web_view.urlChanged.connect(self._on_web_view_url_changed)
        self.web_view.titleChanged.connect(self.title_updated_signal.emit) # Emit title to main window
        self.web_view.loadFinished.connect(self._on_web_view_load_finished)

    def _on_web_view_url_changed(self, qurl):
        # Emit the current URL to the main window's global URL bar
        self.url_updated_signal.emit(qurl)

        # Set specific title if it's the custom homepage URL
        if qurl.toLocalFile() == self.default_page_path:
            self.title_updated_signal.emit("Home") # Or "Monkey-Point Home"

    def _on_web_view_load_finished(self, ok):
        """Simple load finished callback."""
        current_url = self.web_view.url()
        if not ok:
            print(f"Python: Error loading page: {current_url.toString()}")
        else:
            print(f"Python: Page loaded successfully: {current_url.toString()}")
        # Ensure URL is updated in global bar after load
        self.url_updated_signal.emit(current_url)

    def navigate_default_page(self):
        """Loads the local default HTML page."""
        self.web_view.load(QUrl.fromLocalFile(self.default_page_path))


# --- 2. Main Browser Window ---
class MonkeyPointMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monkey-Point Browser")
        # Make the window fullscreen to fill all of the screen
        self.showFullScreen()

        # Central widget container and layout
        self.central_widget_container = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove any extra margins from the main layout

        # --- Global Navigation Bar (moved to top of main window) ---
        self.nav_bar = QWidget()
        self.nav_layout = QHBoxLayout(self.nav_bar)
        self.nav_layout.setContentsMargins(5, 5, 5, 5) # Small margins for the bar itself

        self.back_btn = QPushButton("◀")
        self.forward_btn = QPushButton("▶")
        self.reload_btn = QPushButton("↻")
        self.home_btn = QPushButton("🏠")
        self.url_bar = QLineEdit()
        self.go_btn = QPushButton("Go")

        self.nav_layout.addWidget(self.back_btn)
        self.nav_layout.addWidget(self.forward_btn)
        self.nav_layout.addWidget(self.reload_btn)
        self.nav_layout.addWidget(self.home_btn)
        self.nav_layout.addWidget(self.url_bar)
        self.nav_layout.addWidget(self.go_btn)

        self.main_layout.addWidget(self.nav_bar) # Add global nav bar to the top of the main layout


        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True) # Re-enable Qt's default 'x' for tabs
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setMovable(True)

        # Add "New Tab" button directly to the tab bar (corner)
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(30, 30)
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.new_tab_button, Qt.TopLeftCorner)

        self.main_layout.addWidget(self.tab_widget) # Add tab widget below the nav bar

        self.setCentralWidget(self.central_widget_container) # Set the container as the central widget

        # --- Connect global navigation bar actions ---
        # These buttons operate on the currently active tab's web view
        self.back_btn.clicked.connect(lambda: self._execute_on_current_tab_webview('back'))
        self.forward_btn.clicked.connect(lambda: self._execute_on_current_tab_webview('forward'))
        self.reload_btn.clicked.connect(lambda: self._execute_on_current_tab_webview('reload'))
        self.home_btn.clicked.connect(lambda: self._execute_on_current_tab_webview('navigate_default_page'))

        self.go_btn.clicked.connect(self._navigate_global_url)
        self.url_bar.returnPressed.connect(self._navigate_global_url)

        # Connect tab change signal to update the global URL bar
        self.tab_widget.currentChanged.connect(self._on_tab_changed)


        # Open initial tab
        self.add_new_tab(initial_url="monkey-point://home")

        # Apply stylesheets from external file
        self.apply_global_stylesheet()

    def _execute_on_current_tab_webview(self, action):
        """Helper to execute methods on the current tab's web_view."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            if action == 'back':
                current_tab.web_view.back()
            elif action == 'forward':
                current_tab.web_view.forward()
            elif action == 'reload':
                current_tab.web_view.reload()
            elif action == 'navigate_default_page':
                current_tab.navigate_default_page()

    def apply_global_stylesheet(self):
        """Reads style.css and applies it to the QApplication."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(script_dir, 'style.css')
        try:
            with open(style_path, 'r') as f:
                self.style_sheet = f.read()
            QApplication.instance().setStyleSheet(self.style_sheet)
            print("Python: style.css loaded and applied.")
        except FileNotFoundError:
            print(f"Python Error: style.css not found at {style_path}. UI may not be styled as expected.")
        except Exception as e:
            print(f"Python Error: Failed to apply style.css: {e}")

    def add_new_tab(self, initial_url=None):
        """Adds a new tab to the browser."""
        browser_tab = BrowserTab(self)
        index = self.tab_widget.addTab(browser_tab, "Loading...")

        # Connect this new tab's signals to the main window's global URL bar and tab titles
        browser_tab.url_updated_signal.connect(self._update_global_url_bar)
        browser_tab.title_updated_signal.connect(
            lambda title: self.tab_widget.setTabText(index, title or "New Tab")
        )

        if initial_url == "monkey-point://home":
            browser_tab.navigate_default_page()
        elif initial_url:
            browser_tab.web_view.load(QUrl(initial_url))
        else:
            browser_tab.navigate_default_page()

        self.tab_widget.setCurrentIndex(index)
        # Update global URL bar immediately when new tab is added/becomes current
        self._update_global_url_bar(browser_tab.web_view.url())


    def close_tab(self, index):
        """Closes the specified tab."""
        if self.tab_widget.count() < 2:
            reply = QMessageBox.question(self, 'Close Browser',
                                         "This is the last tab. Do you want to close the browser?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.close()
            return

        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater() # Ensures widget is properly disposed

    def _navigate_global_url(self):
        """Handles global navigation based on URL bar input."""
        current_tab = self.tab_widget.currentWidget()
        if not current_tab: # Should not happen if at least one tab is always open
            return

        url_text = self.url_bar.text().strip()
        if not url_text:
            current_tab.navigate_default_page()
            return

        # Handle custom 'monkey-point://home' scheme if typed directly
        if url_text.lower() == "monkey-point://home":
            current_tab.navigate_default_page()
            return

        # Logic for searching vs direct URL
        if ("." in url_text and " " not in url_text) or url_text.startswith(('http://', 'https://', 'ftp://', 'file:///')):
            if not url_text.startswith(('http://', 'https://')):
                final_url = "http://" + url_text
            else:
                final_url = url_text
        else:
            search_query = QUrl.toPercentEncoding(url_text)
            final_url = f"https://duckduckgo.com/?q={search_query.data().decode('utf-8')}"

        print(f"Python: Global Navigating to: {final_url}")
        current_tab.web_view.load(QUrl(final_url))

    def _on_tab_changed(self, index):
        """Updates global URL bar when the active tab changes."""
        if index >= 0:
            current_tab = self.tab_widget.widget(index)
            if current_tab:
                # Update the URL bar to reflect the newly selected tab's current URL
                current_url = current_tab.web_view.url()
                if current_url.toLocalFile() == current_tab.default_page_path:
                    self.url_bar.setText("monkey-point://home")
                else:
                    self.url_bar.setText(current_url.toString())
                    self.url_bar.setCursorPosition(0) # Ensure cursor is at start
        else: # No tabs left or invalid index
            self.url_bar.setText("")

    def _update_global_url_bar(self, qurl):
        """Updates the global URL bar with the URL from the active tab.
           This method is connected to the 'url_updated_signal' of each BrowserTab."""
        current_tab = self.tab_widget.currentWidget()
        # Only update if the signal is from the *currently active* tab
        # This prevents background tabs from updating the main URL bar
        if current_tab and current_tab.web_view.url() == qurl:
            if qurl.toLocalFile() == current_tab.default_page_path:
                self.url_bar.setText("monkey-point://home")
            else:
                self.url_bar.setText(qurl.toString())
                self.url_bar.setCursorPosition(0)


# --- 3. Application Entry Point ---
if __name__ == "__main__":
    # Enable high DPI scaling for better appearance on high-resolution screens
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("Monkey-Point Browser")
    browser = MonkeyPointMainWindow()
    # browser.show() is handled by showFullScreen() inside the __init__
    sys.exit(app.exec_())