import os


# Get environment (default to 'dev' if not set)
FLASK_ENV = os.getenv("FLASK_ENV", "dev")


def get_page_info(pageName):
    """
    Returns configuration details based on page name.
    """

    info = {

        "configuration": {
            "tempdir_path": f"/appfs/{FLASK_ENV}/config_repo",
            "targetdir_path": f"/appfs/{FLASK_ENV}/Lumos/Configurations",
            "git_branch_name": "Test_Configurations",
            "path": f"/appfs/{FLASK_ENV}/Lumos/Configurations",
            "source_subfolder": "configurations"
        },

        "sample": {
            "tempdir_path": f"/appfs/{FLASK_ENV}/sample_repo",
            "targetdir_path": f"/appfs/{FLASK_ENV}/Lumos/sample",
            "git_branch_name": "Test_Sample",
            "path": f"/appfs/{FLASK_ENV}/Lumos/sample",
            "source_subfolder": "sample"
        },

        "executionlog": {
            "path": f"/appfs/{FLASK_ENV}/Lumos/Logs"
        },

        "executionreports": {
            "path": f"/appfs/{FLASK_ENV}/Lumos/Executions"
        },

        "executiondetails": {
            "path": f"/appfs/{FLASK_ENV}/Lumos/Executions"
        }
    }

    default_info = {
        "tempdir_path": f"/appfs/{FLASK_ENV}/config_repo",
        "targetdir_path": f"/appfs/{FLASK_ENV}/Lumos/Configurations",
        "git_branch_name": "Test_Configurations",
        "path": f"/appfs/{FLASK_ENV}/Lumos/Configurations",
        "source_subfolder": "configurations"
    }

    if not pageName:
        return default_info

    return info.get(pageName.lower(), default_info)
