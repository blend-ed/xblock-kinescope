"""This XBlock embeds content from Kinescope through Iframes"""
import json

from django.core.exceptions import ValidationError
from django.template import Context, Template
from django.conf import settings
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, Dict
from xblock.completable import CompletableXBlockMixin
from xblock.validation import ValidationMessage
from webob import Response

try:
    # Older Open edX releases (Redwood and earlier) install a backported version of
    # importlib.resources: https://pypi.org/project/importlib-resources/
    import importlib_resources
except ModuleNotFoundError:
    # Starting with Sumac, Open edX drops importlib-resources in favor of the standard library:
    # https://docs.python.org/3/library/importlib.resources.html#module-importlib.resources
    from importlib import resources as importlib_resources

from .utils import _, validate_parse_kinescope_url, get_video_list


api_key = settings.KINESCOPE_API_KEY


@XBlock.wants("settings")
class KinescopeXBlock(XBlock, CompletableXBlockMixin):
    """
    This XBlock renders Iframe for Kinescope videos.
    """

    video_link = String(
        display_name="Video Link/URL",
        default="",
        scope=Scope.settings,
        help=_("Choose video from the list.")
    )

    display_name = String(
        display_name="Display Name",
        default="Kinescope Video",
        scope=Scope.settings,
        help=_("Display name for the video.")
    )

    has_author_view = True

    def validate_field_data(self, validation, data):
        """
        Validate video link and video id
        """
        if not data.video_link:
            validation.add(ValidationMessage(ValidationMessage.ERROR, _("Video Link is mandatory")))
        else:
            try:
                validate_parse_kinescope_url(data.video_link)
            except ValidationError as e:
                for msg in e.messages:
                    validation.add(ValidationMessage(ValidationMessage.ERROR, msg))


    def render_template(self, template_path, context):
        template_str = self.resource_string(template_path)
        template = Template(template_str)
        return template.render(Context(context))


    @staticmethod
    def resource_string(path):
        """Handy helper for getting static resources from our kit."""
        data = importlib_resources.files(__name__).joinpath(path).read_bytes()
        return data.decode("utf8")
    

    def student_view(self, context=None):
        """
        The primary view of the KinescopeXBlock, shown to students
        when viewing courses.
        """
        video_list = get_video_list(api_key)
        
        try:
            video_id = validate_parse_kinescope_url(self.video_link)
        except ValidationError:
            print(f"Invalid video link: {self.video_link}")
            video_id = ""

        if video_id == "":
            context = {
                'kinescope': self,
                'display_name': self.display_name,
                'video_list': video_list,
            }
        else:
            context = {
                'kinescope': self,
                'video_id': video_id,
                'display_name': self.display_name,
                'video_list': video_list,
            }

        template = self.render_template("static/html/kinescope.html", context)
        frag = Fragment(template)
        frag.add_css(self.resource_string("public/css/kinescope.css"))
        frag.add_javascript(self.resource_string("public/js/kinescope.js"))
        frag.initialize_js('KinescopeXBlock')
        return frag
    
    def author_view(self, context=None):
        """
        The primary view of the KinescopeXBlock, shown to instructors.
        """

        return self.student_view(context)

    def studio_view(self, context=None):
        """
        The primary view of the KinescopeXBlock, shown to instructors.
        """
        video_list = get_video_list(api_key)
        context = {
            'kinescope': self,
            'video_link': self.fields['video_link'],
            'display_name': self.fields['display_name'],
            'video_list': video_list,
        }

        template = self.render_template("static/html/kinescope_studio.html", context)
        frag = Fragment(template)
        frag.add_css(self.resource_string("public/css/kinescope.css"))
        frag.add_javascript(self.resource_string("public/js/kinescope_studio.js"))
        frag.initialize_js('KinescopeStudioXBlock')
        return frag


    @staticmethod
    def json_response(data):
        return Response(
            json.dumps(data), content_type="application/json", charset="utf8"
        )
    

    @XBlock.handler
    def studio_submit(self, request, _suffix):
        """
        Save the video link and display name
        """
        self.video_link = request.params.get('video_link')
        self.display_name = request.params.get('display_name')
        
        return self.json_response({'status': 'success', 'errors': []})
    

    @XBlock.handler
    def upload_video(self, request, suffix=''):
        """
        Upload video file
        """
        video_file = request.params.get('video_file')
        self.video_file = video_file
        return self.json_response({'status': 'success', 'errors': []})


    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "KinescopeXBlock",
                """<vertical_demo>
                <kinescope/>
                </vertical_demo>
             """,
            ),
        ]


    @property
    def xblock_settings(self):
        """
        Return a dict of settings associated to this XBlock.
        """
        settings_service = self.runtime.service(self, "settings") or {}
        if not settings_service:
            return {}
        return settings_service.get_settings_bucket(self)