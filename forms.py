from flask_wtf import FlaskForm
from wtforms import FloatField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class ComplianceTextForm(FlaskForm):
    """Form for managing compliance text sections."""

    section = StringField("Section Name", validators=[DataRequired()])
    text = TextAreaField(
        "Compliance Text",
        validators=[DataRequired()],
        description="Legal text or compliance information",
    )
    submit = SubmitField("Save Text")


class OutputTemplateForm(FlaskForm):
    """Form for managing report output templates."""

    name = StringField("Template Name", validators=[DataRequired()])
    content = TextAreaField(
        "Template Content",
        validators=[DataRequired()],
        description="Template content using markdown with placeholders like {loan_amount}",
    )
    submit = SubmitField("Save Template")


class LoginForm(FlaskForm):
    """Form for admin login."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class FeesForm(FlaskForm):
    """Form for managing fees and closing costs."""

    fee_type = SelectField(
        "Fee Type",
        choices=[
            ("origination", "Origination Fee"),
            ("appraisal", "Appraisal Fee"),
            ("credit_report", "Credit Report Fee"),
            ("title", "Title Fee"),
            ("recording", "Recording Fee"),
            ("other", "Other Fee"),
        ],
        validators=[DataRequired()],
    )
    name = StringField("Fee Name", validators=[DataRequired()])
    amount = FloatField(
        "Amount",
        validators=[DataRequired(), NumberRange(min=0)],
        description="Fee amount in dollars",
    )
    is_percentage = SelectField(
        "Fee Type",
        choices=[("fixed", "Fixed Amount"), ("percentage", "Percentage of Loan")],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Save Fee")
