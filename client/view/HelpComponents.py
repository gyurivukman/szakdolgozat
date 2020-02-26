from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QFont, QPixmap


class AccountHelpPageBase(QWidget):

    def __init__(self):
        super().__init__()
        self.__stepFont = QFont("Nimbus Sans L", 12, False)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("self")
        self.setStyleSheet(
            """
                QWidget#self{border:none; background-color:white;} 
                QLabel#figure{border:2px solid #e36410;}
            """
        )
        self._steps = self._createSteps()
        self._setup()
    
    def _createSteps(self):
        raise NotImplementedError(f"Derived class {self.__class__} must implement method '_createSteps'. It should return a List[dict[str, str]]")

    def _setup(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 3, 3, 3)
        layout.setSpacing(20)

        for step in self._steps:
            layout.addWidget(self._createFixedWidthStep(step['text']))
            if step['figure']:
                layout.addWidget(self._createFigure(step['figure']))

        self.setLayout(layout)

    def _createFixedWidthStep(self, stepString):
        step = QLabel(stepString)
        step.setFont(self.__stepFont)
        step.setFixedWidth(550)
        step.setOpenExternalLinks(True)
        step.setWordWrap(True)

        return step

    def _createFigure(self, imagePath):
        figure = QLabel()
        figure.setObjectName("figure")
        figurePixmap = QPixmap(imagePath)
        figure.setPixmap(figurePixmap)

        return figure


class DropboxHelpPage(AccountHelpPageBase):
    
    def _createSteps(self):
        return [
            {
                "text": "1. If you do not have an account, go to <a href=\"www.dropbox.com\">www.dropbox.com</a> and register a new account.",
                "figure": None
            },
            {
                "text": "2. Sign it with your newly created account.",
                "figure": None
            },
            {
                "text": "3. Navigate to the following page: <a href=\"https://www.dropbox.com/developers/apps\">Dropbox Developer Console</a>.",
                "figure": None
            },
            {
                "text": "4. Create a new application by clicking the \"Create App\" button.",
                "figure": ":dropboxhelp/figure_1_click_create_app.png"
            },
            {
                "text": "5. Fill out the application form as below. You can give any name to your application.",
                "figure": ":dropboxhelp/figure_2_fill_out_the_form.png"
            },
            {
                "text": "6. After clicking Create App, click \"Generate\" to create an access token.",
                "figure": ":dropboxhelp/figure_3_api_token.png"
            },
            {
                "text": "7. Copy and paste this Api token into the Dropbox API Access Token input field on the dropbox account form.",
                "figure": None
            }
        ]


class DriveHelpPage(AccountHelpPageBase):

    def _createSteps(self):
        return [
            {
                "text": "1. If you do not have a Google account or you wish to use a new account with CryptStorePi, follow <a href=\"https://accounts.google.com/signup\">this link and register a new account.</a>",
                "figure": None
            },
            {
                "text": "2. Sign in with your newly created google account at <a href=\"https://console.cloud.google.com/\">this link.</a>",
                "figure": None
            },
            {
                "text": "3. On the top navigation bar, click \"Create project\".",
                "figure": ":drivehelp/figure_1_create_project.png"
            },
            {
                "text": "4. Name your project and click \"Create\".",
                "figure":None
            },
            {
                "text": "5. Open the <a href=\"https://console.developers.google.com/\">developer console</a> ",
                "figure":None
            },
            {
                "text": "6. Select your newly created project from the dropdown menu at the top, then click 'Enable APIs and Services'.",
                "figure": ":drivehelp/figure_2_selecting_project.png"
            },
            {
                "text": "7. Search for 'Google Drive Api', then click on the result.",
                "figure": ":drivehelp/figure_3_searching_for_api.png"
            },
            {
                "text": "8. Enable the 'Google Drive Api' for your project.",
                "figure": ":drivehelp/figure_4_enabling_api.png"
            },
            {
                "text": "9. Select 'IAM&admin/Service Accounts' from the dropdown menu at the top left. Then click 'Create service account' and give it any name.",
                "figure": ":drivehelp/figure_5_service_accounts_menu.png"
            },
            {
                "text": "10. Add two roles: Project Editor and Monitoring Editor.",
                "figure": ":drivehelp/figure_6_service_account_roles.png"
            },
            {
                "text": "11. Create a key for this service account.",
                "figure": ":drivehelp/figure_7_create_service_key.png"
            },
            {
                "text": "12. Locate and open the downloaded file with the 'Open Credentials File' button.",
                "figure":None
            }
        ]
