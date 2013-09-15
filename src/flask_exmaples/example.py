from yota.nodes import *
import yota
from yota import Form
from yota.validators import *
from yota.renderers import JinjaRenderer
import os
import vals
import pickle
from flask import Flask, request, render_template, send_from_directory, abort, session, send_file
from pysistor import Pysistor
from StringIO import StringIO
app = Flask(__name__)
pysistor.Pysistor.from_dict(backend="pysistor.backends.FlaskSessionBackend",
                            set_default=True)

# Patch out jinjarenderer to include templates that are local. This is the
# standard implementation for modifying search path to include templates
JinjaRenderer.search_path.insert(0, os.path.dirname(os.path.realpath(__file__)) +
"/templates/yota/")

@app.route('/yota_static/<path:filename>')
def custom_static(filename):
    """ Setup a custom static route to grab the JavaScript library from Yota.
    Somewhat hackey and magical, but it works. """
    return send_from_directory(os.path.dirname(yota.__file__), filename)

@app.route("/dynamic", methods=['GET', 'POST'])
def dynamic():

    # Handle submission of the form
    if request.method == 'POST':
        # This may be a bit confusing. Essentially we're using the data
        # submitted with the request to build our object representation of the
        # form. This is the magic of dynamic forms that allows them to match a
        # changing form based on parameters
        form = DynamicForm.get_form_from_data(request.form)
        # Then we validate the form just like the old AJAX form
        success, output = form.json_validate(request.form)
        if success:
            print ("Yay! Successfully validated. Some other actions should be "
                  " taken here...")
        return output

    # Generate the form as default if there's no submission
    form_out = DynamicForm.get_form().render()

    return render_template('dynamic.html',
                            form=form_out)

class DynamicForm(Form):
    # simple header trigger for the template
    title = "Dynamic Form"
    g_context={'ajax': True}
    class AddNodeDynamic(NonDataNode):
        """ This is our custom Node that allows the addition of other Nodes. It
        basically runs some javascript that clones the pre-existing Node,
        changes some parameters, and then re-injects it. It could use some
        improvement as it's just for demonstration. In the future some of this
        could be genericized and mainlined into the library, but for now this
        demonstrates the potential.

        Also note that it inherits from NonDataNode since it doesn't generate
        any output. This will prevent a DataAccessException on submission.
        """
        template = "dynamic_add"

    @classmethod
    def get_form_from_data(cls, data):
        # This function looks for any hidden fields that were submitted with
        # the prefix _arg_ and turns them into kwargs that were used to
        # generate the form. Essentially we're storing the important parameters
        # used to generate the form in hidden input fields
        kwargs = {}
        # loop over all our data
        for key, val in data.iteritems():
            if key.startswith('_arg_'):
                # Chop off the _arg_ part and add it to kwargs
                kwargs[key[5:]] = val
        # return the generated form
        return cls.get_form(**kwargs)

    @classmethod
    def get_form(cls, count=1, **kwargs):
        # a method that allows us to repeatably build a dynamic form based on
        # parameters.

        # Build our basic form
        form = DynamicForm(hidden={'count': count})

        # Make a list of nodes to add into the Form nodelist
        append_list = []
        for i in xrange(int(count)):
            # Add a new entry node to it
            append_list.append(
                EntryNode(title="Item {0}".format(i), _attr_name='item{0}'.format(i)))
            # Also add a validator. At this point cannot be added through the
            # shorthand with dynamic nodes. To come in the future
            form.insert_validator(Check(MinLengthValidator(5), 'item{0}'.format(i)))

        # Now insert our list of nodes. We could also have just inserted them
        # one by one in the loop above, this was simply to demonstrate that the
        # insert method accepts a list
        form.insert_after('l_title', append_list)
        return form

    # Accept a simple title that requires minlength
    l_title = EntryNode(title="List Title", validators=MinLengthValidator(5))
    # Our button that adds a row
    add_row = AddNodeDynamic()
    # Notice that we don't have a single entrynode. This will be created by the
    # default args for get_form, since we notice that count=1
    submit = SubmitNode(title="Submit")

    def success_header_generate(self):
        return {'message': 'Thanks for your submission!'}

@app.route("/captcha/<tident>", methods=['GET', 'POST'])
def captcha_image(tident=None):
    # Fetch the test object from pysistor
    test = pickle.loads(Pysistor[None].get("captcha_{0}".format(tident)))
    sfile = StringIO()
    test.render().save(sfile, 'JPEG', quality=70)
    sfile.seek(0)
    return send_file(sfile, mimetype='image/jpeg')

@app.route("/basic", methods=['GET', 'POST'])
def basic():
    # Create an instance of our Form class
    form = BasicForm()

    # Handle submission of the form
    if request.method == 'POST':
        # Run our convenience method designed for regular forms
        # success is boolean if validation passed, out is the re-rendering of
        # the form
        success, out = form.validate_render(request.form)
        # This is where actions should be taken on the form
        if success:
            print "Whoo! We should do some sort of database stuff here..."
    else:
        # By default we just render an empty form
        out = form.render()

    def success_header_generate(self):
        return {'message': 'Thanks for your submission!'}

    return render_template('basic.html',
                            form=out)


class BasicForm(Form):
    # Triggers a simple h2 header
    title = "Basic Form"

    # Override the default title which would be "First" to "First Name"
    first = EntryNode(title="First Name")
    # And add a validator to it explicitly. The name of the attribute is not important
    _last_valid = Check(MinLengthValidator(5), 'first')
    # Like above, but now add a simple shorthand for a min length validator
    last = EntryNode(title="Last Name", validators=MinLengthValidator(5))
    # Now add a different type of validator. Simply requires your submission to not be nothing
    address = EntryNode(validators=RequiredValidator())
    # Make a dropdown that lists all the states. Pull in the data from another
    # file for cleanlyness
    state = ListNode(items=vals.states)
    # Captcha node to detect robot people
    captch = CaptchaNode(validators=CaptchaValidator())
    captch_remove = Listener(
        "validate_success", captcha_success_trigger, "captch")

    submit = SubmitNode(title="Submit")

    def success_header_generate(self):
        self.start.add_error({'message': 'Thanks for your submission!'})


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')


class JsonForm(Form):
    # must be in place to tell our form we're doing piecewise. Activates
    # certain things in the rendering proccess
    g_context = {'piecewise': True, 'ajax': True}

    # Set a simple title for the form
    title = 'User signup <small>(not really)</small>'

    first = EntryNode(title="First Name", validators=MaxLengthValidator(32))
    last = EntryNode(title="Last Name", validators=MaxLengthValidator(32))
    password = PasswordNode(title='Password*',
                            validators=MinMaxValidator(5,32))
    password_confirm = PasswordNode(title='Password Confirm*',
                                   validators=MinMaxValidator(5,32))
    # Setup a password validator that requires two matching fields
    _passwords_match = Check(MatchingValidator(),
                             'password',
                             'password_confirm')
    email = EntryNode(validators=EmailValidator(), title='Email*')
    address = EntryNode()
    state = ListNode(items=vals.states)
    zip = EntryNode(title="Zipcode*",
                    validators=[IntegerValidator(),
                               MinMaxValidator(5, 5)])
    terms = CheckGroupNode(
        boxes=[('news', 'Recieve our newsletter?'),
               ('dont_agree', 'Something else you don\'t want to check?'),
               ('agree', '<b>Agree to our terms of service?*</b>')])

    submit = SubmitNode(title="Submit")

    # When all validator pass this data will be used in our render_success
    # javascript callback. More information on how this works in the AJAX
    # documentation
    def success_header_generate(self):
        return {'message': 'Thanks for your submission!'}


@app.route("/piecewise", methods=['GET', 'POST'])
def piecewise():
    # Generate a regular form via a classmethod to provide easy access to extra
    # functionality
    form = JsonForm()

    # Handle regular submission of the form
    if request.method == 'POST':
        success, out = form.json_validate(request.form, piecewise=True)
        if success:
            print "Whoo! We should do some sort of database stuff here..."

        return out
    else:
        out = form.render()

    return render_template('piecewise.html',
                            form=out)

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
    app.debug = True
    app.run()
