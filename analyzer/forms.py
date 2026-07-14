from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class UploadProjectForm(forms.Form):

    project_name = forms.CharField(
        max_length=255,
        label="Project Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Employee Management System",
            }
        ),
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Optional project description...",
            }
        ),
    )

    zip_file = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": ".zip",
            }
        ),
    )

    files = forms.FileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "accept": ".py",
            }
        ),
    )

    def clean(self):

        cleaned_data = super().clean()

        zip_file = cleaned_data.get("zip_file")

        uploaded_files = self.files.getlist("files")

        if not zip_file and not uploaded_files:
            raise forms.ValidationError(
                "Upload either a ZIP file or one or more Python files."
            )

        if zip_file:

            if not zip_file.name.lower().endswith(".zip"):
                raise forms.ValidationError(
                    "Only ZIP files are allowed."
                )

        for file in uploaded_files:

            if not file.name.lower().endswith(".py"):

                raise forms.ValidationError(
                    f"{file.name} is not a Python file."
                )

        return cleaned_data