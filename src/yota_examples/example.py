from yota import Form
from yota.nodes import *
import yota
from yota.validators import *
from yota.renderers import JinjaRenderer
import os
import vals
from flask import Flask, request
from flask import render_template, send_from_directory
import piecewise
app = Flask(__name__)

# Patch out jinjarenderer to include templates that are local
JinjaRenderer.search_path.insert(0, os.path.dirname(os.path.realpath(__file__)) +
"/templates/yota/")

""" Setup a custom static route to grab the JavaScript library from Yota.
Somewhat hackey, but it works. """
@app.route('/yota_static/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.dirname(yota.__file__), filename)

class JsonForm(Form):
    @classmethod
    def get_form(cls, name, mode=0):
        # Populate our global context depending on values
        g_context = {}
        if mode == 0:
            g_context['ajax'] = True
        elif mode == 1:
            g_context['ajax'] = True
            g_context['piecewise'] = True

        f = JsonForm(name=name,
                id=name,
                g_context=g_context,
                hidden={'name': name})
        return f

    first = EntryNode(title="First Name", validators=MinLengthValidator(5))
    last = EntryNode(title="Last Name")
    _last_valid = Check(MinLengthValidator(5), 'last')
    address = EntryNode(validators=RequiredValidator())
    state = ListNode(items=vals.states)
    submit = SubmitNode(title="Submit")

    def process_validation(self, vdict):
        if 'message' not in vdict:
            vdict['message'] = 'Please enter a valid value.'
        return vdict

class DynamicForm(Form):
    class AddNodeDynamic(Node):
        template = "dynamic_add"

    @classmethod
    def get_form_from_data(cls, data):
        kwargs = {}
        for key, val in data.iteritems():
            if key.startswith('_arg_'):
                kwargs[key[5:]] = val
        return cls.get_form(**kwargs)

    @classmethod
    def get_form(cls, count=1, **kwargs):
        # Make a list of nodes to add into the Form nodelist
        append_list = []
        form = DynamicForm(g_context={'ajax': True},
                           name='dynamic',
                           hidden={'count': count, 'dynamic': True})
        for i in xrange(int(count)):
            append_list.append(
                EntryNode(title="Item {0}".format(i), _attr_name='item{0}'.format(i)))
            form._validation_list.append(Check(MinLengthValidator(5), 'item{0}'.format(i)))

        form.insert_after('title', append_list)
        return form

    title = EntryNode(title="List Title", validators=MinLengthValidator(5))
    add_row = AddNodeDynamic()
    submit = SubmitNode(title="Submit")

class BasicForm(Form):
    # Override the default title which would be "First" to "First Name"
    first = EntryNode(title="First Name")
    # And add a validator to it explicitly. The name of the attribute is not important
    _last_valid = Check(MinLengthValidator(5), 'first')
    # Like above, but now add a simple shorthand for a min length validator
    last = EntryNode(title="Last Name", validators=MinLengthValidator(5))
    # Now add a different type of validator. Simply requires your submission to not be nothing
    address = EntryNode(validators=RequiredValidator())
    state = ListNode(items=vals.states)
    submit = SubmitNode(title="Submit")

@app.route("/", methods=['GET', 'POST'])
def home():
    """ The block of logic below is unfortunately somewhat confusing, but most
    of its clutter comes from the fact that we have four forms on the same page,
    and all of them have slightly different way in which they need to be
    invoked. """

    # Generate a regular form via a classmethod to provide easy access to extra functionality
    basic_form = BasicForm()
    submit_form = JsonForm.get_form('regular')
    piecewise_form = JsonForm.get_form('ajax', mode=1)

    # Handle regular submission of the form
    if request.method == 'POST':
        if '_arg_dynamic' in request.form:
            form_out = DynamicForm.get_form_from_data(request.form)
            return form_out.json_validate(request.form)
        elif '_piecewise_' in request.form:
            return piecewise_form.json_validate(request.form, piecewise=True)
        elif '_ajax_' in request.form:
            return submit_form.json_validate(request.form)
        else:
            basic_form_out = basic_form.validate_render(request.form)
    else:
        basic_form_out = basic_form.render()

    # Generate a regular form via a classmethod to provide easy access to extra functionality
    dynamic_form = DynamicForm.get_form()

    return render_template('index.html',
                            basic_form=basic_form_out,
                            dynamic_form=dynamic_form.render(),
                            piecewise_form=piecewise_form.render(),
                            submit_form=submit_form.render())



class JsonForm2(Form):
    # must be in place to tell our form we're doing piecewise. Activates
    # certain things in the rendering proccess
    g_context = {'piecewise': True, 'ajax': True}

    # Set a simple title for the form
    title = 'User signup <small>(not really)</small>'

    first = EntryNode(title="First Name", validators=MaxLengthValidator(32))
    last = EntryNode(title="Last Name", validators=MaxLengthValidator(32))
    password = PasswordNode(title='Password*',
                            validators=MinMaxValidator(5,32))
    password_confim = PasswordNode(title='Password Confirm*',
                                   validators=MinMaxValidator(5,32))
    _passwords_match = Check(MatchingValidator(),
                             'password',
                             'password_confirm')
    email = EntryNode(validators=EmailValidator(), title='Email*')
    address = EntryNode(validators=RequiredValidator())
    state = ListNode(items=vals.states)
    zip = EntryNode(validators=[IntegerValidator(),
                               MinMaxValidator(5, 5)])
    terms = CheckGroupNode(
        boxes=[('news', 'Recieve our newsletter?'),
               ('dont_agree', 'Something else you don\'t want to check?'),
               ('agree', '<b>Agree to our terms of service?*</b>')])

    submit = SubmitNode(title="Submit")

    def process_validation(self, vdict):
        if 'message' not in vdict:
            vdict['message'] = 'Please enter a valid value.'
        return vdict


@app.route("/piecewise", methods=['GET', 'POST'])
def piecewise():
    # Generate a regular form via a classmethod to provide easy access to extra
    # functionality
    form = JsonForm2()

    # Handle regular submission of the form
    if request.method == 'POST':
        return form.json_validate(request.form, piecewise=True)
    else:
        out = form.render()

    return render_template('piecewise.html',
                            form=out)



if __name__ == "__main__":
    app.debug = True
    app.run()
