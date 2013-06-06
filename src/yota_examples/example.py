from yota import Form
from yota.nodes import *
import yota
from yota.validators import Check, MinLengthValidator, RequiredValidator
import os
import vals
from flask import Flask, request
from flask import render_template, send_from_directory
app = Flask(__name__)

""" Setup a custom static route to grab the JavaScript library from Yota.
Somewhat hackey, but it works. """
@app.route('/yota_static/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.dirname(yota.__file__), filename)

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

""" ================================================================================= """
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

@app.route("/basic", methods=['GET', 'POST'])
def basic():
    # Generate a regular form via a classmethod to provide easy access to extra functionality
    form = BasicForm()
    # Handle regular submission of the form
    if request.method == 'POST':
        form_out = form.validate_render(request.form)
    else:
        form_out = form.render()

    # Generate our ajax form
    return render_template('basic.html', form=form.render())

""" ================================================================================= """
class DynamicForm(Form):
    @classmethod
    def get_form_from_data(cls, data):
        args = []
        for key, val in data.iteritems():
            if key.startswith('_arg_'):
                args.append(val)
        return cls.get_form(*args)

    @classmethod
    def get_form(cls, name, mode=0, count=1):
        # Make a list of nodes to add into the Form nodelist
        append_list = []
        for i in xrange(int(count)):
            append_list.append(
                EntryNode(title="Item {}".format(i), _attr_name='item{}'.format(i)))

        # Populate our global context depending on values
        g_context = {'ajax': True}

        form = DynamicForm(name=name,
                        id=name,
                        g_context=g_context,
                        hidden={'name': name,
                                'count': count})
        form.insert_after('address', append_list)
        return form

    first = EntryNode(title="First Name", validators=MinLengthValidator(5))
    last = EntryNode(title="Last Name")
    _last_valid = Check(MinLengthValidator(5), 'last')
    address = EntryNode(validators=RequiredValidator())
    state = ListNode(items=vals.states)
    submit = SubmitNode(title="Submit")

@app.route("/dynamic", methods=['GET', 'POST'])
def dynamic():
    # Generate a regular form via a classmethod to provide easy access to extra functionality
    form_out = DynamicForm()
    # Handle regular submission of the form
    if request.method == 'POST':
        form_out = form_out.validate_render(request.form)
    else:
        form_out = form_out.render()

    # Generate our form
    return render_template('dynamic.html', form=form_out)

""" ================================================================================= """
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

@app.route("/json", methods=['GET', 'POST'])
def json():
    # Generate a regular form via a classmethod to provide easy access to extra functionality
    submit_form = JsonForm.get_form('regular')
    piecewise_form = JsonForm.get_form('ajax', mode=1)

    # Handle regular submission of the form
    if request.method == 'POST' and '_piecewise_' in request.form:
        return piecewise_form.json_validate(request.form, piecewise=True)
    elif '_ajax_' in request.form:
        return submit_form.json_validate(request.form)

    # just return the regular render of our page
    return render_template('json.html', submit_form=submit_form.render(), piecewise_form=piecewise_form.render())


if __name__ == "__main__":
    app.debug = True
    app.run()
