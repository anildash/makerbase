import json
import traceback

from flask import abort, request, Response
from flask.views import MethodView
from flaskext.login import login_required
from werkzeug.datastructures import MultiDict

from makerbase import app
from makerbase.forms import MakerForm, ProjectForm, ParticipationForm, ProjectAddParticipationForm
from makerbase.models import Robject
from makerbase.models import *


class RobjectView(MethodView):

    def dispatch_request(self, *args, **kwargs):
        try:
            return super(RobjectView, self).dispatch_request(*args, **kwargs)
        except Exception, exc:
            return Response(json.dumps({
                "errors": [traceback.format_exc().split('\n')],
            }), 500)

    @staticmethod
    def json_plus_robjects(obj):
        if isinstance(obj, Robject):
            return obj.get_api_data()
        raise TypeError('%r is not a robject' % obj)

    def render(self, obj):
        return json.dumps(obj, default=self.json_plus_robjects)


class ResourceView(RobjectView):

    def get(self, slug):
        obj = self.objclass.get(slug)
        if obj is None:
            abort(404)
        return self.render(obj)

    @login_required
    def post(self, slug):
        obj = self.objclass.get(slug)
        if obj is None:
            abort(404)

        data = json.loads(request.data)
        form = self.formclass(MultiDict(data), obj)
        if not form.validate():
            return Response(json.dumps({
                'errors': form.errors,
            }), 400)

        form.populate_obj(obj)
        obj.save()

        return self.render(obj)

    @login_required
    def put(self, slug):
        data = json.loads(request.data)
        form = self.formclass(MultiDict(data))
        if not form.validate():
            return Response(json.dumps({
                'errors': form.errors,
            }), 400)

        obj = self.objclass.get(slug)
        if obj is None:
            obj = self.objclass(slug)
        form.populate_obj(obj)
        obj.save()

        return self.render(obj)


class MakerAPI(ResourceView):

    objclass = Maker
    formclass = MakerForm


class ProjectAPI(ResourceView):

    objclass = Project
    formclass = ProjectForm


class ParticipationAPI(ResourceView):

    objclass = Participation
    formclass = ParticipationForm


class ProjectPartiesAPI(RobjectView):

    def get(self, slug):
        proj = Project.get(slug)
        if proj is None:
            abort(404)
        return self.render(list(proj.parties))

    @login_required
    def post(self, slug):
        proj = Project.get(slug)
        if proj is None:
            abort(404)

        data = json.loads(request.data)
        form = ProjectAddParticipationForm(MultiDict(data))
        if not form.validate():
            return Response(json.dumps({
                'errors': form.errors,
            }), 400)

        party = Participation()
        form.populate_obj(party)
        del party.maker
        party.add_link(proj, tag='project')

        maker = Maker.get(form.maker.data)
        if maker is None:
            return Response(json.dumps({
                'errors': {
                    'maker': ['Maker ID is invalid'],
                }
            }), 400)
        party.add_link(maker, tag='maker')
        party.save()

        maker.add_link(party, tag='participation')
        maker.save()
        proj.add_link(party, tag='participation')
        proj.save()
        return self.render(party)


app.add_url_rule('/api/maker/<slug>', view_func=MakerAPI.as_view('api_maker'))
app.add_url_rule('/api/project/<slug>', view_func=ProjectAPI.as_view('api_project'))
app.add_url_rule('/api/project/<slug>/parties', view_func=ProjectPartiesAPI.as_view('api_project_parties'))
app.add_url_rule('/api/participation/<slug>', view_func=ParticipationAPI.as_view('api_participation'))
