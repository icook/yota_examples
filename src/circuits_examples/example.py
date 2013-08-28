#!/usr/bin/env python

import os

from yota import Form
from yota.nodes import *  # noqa
from yota.validators import *  # noqa
from yota.renderers import JinjaRenderer

from jinja2 import Environment, FileSystemLoader

from circuits.web import Controller, Server, Static

import vals

# Patch out jinjarenderer to include templates that are local. This is the
# standard implementation for modifying search path to include templates
JinjaRenderer.search_path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/yota/")
)

env = Environment(loader=FileSystemLoader("templates"))


def render_template(name, **ctx):
    template = env.get_template(name)
    return template.render(**ctx)


class DynamicForm(Form):

    # simple header trigger for the template
    title = "Dynamic Form"
    g_context = {'ajax': True}

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


class BasicForm(Form):
    # Triggers a simple h2 header
    title = "Basic Form"

    # Override the default title which would be "First" to "First Name"
    first = EntryNode(title="First Name")
    # And add a validator to it explicitly. The name of the attribute is not important
    _last_valid = Check(MinLengthValidator(5), 'first')
    # Like above, but now add a simple shorthand for a min length validator
    last = EntryNode(title="Last Name", validators=MinLengthValidator(5))
    # Now add a different type of validator.
    # Simply requires your submission to not be nothing
    address = EntryNode(validators=RequiredValidator())
    # Make a dropdown that lists all the states. Pull in the data from another
    # file for cleanlyness
    state = ListNode(items=vals.states)
    submit = SubmitNode(title="Submit")

    def success_header_generate(self):
        self.start.add_error({'message': 'Thanks for your submission!'})


class JsonForm(Form):
    # must be in place to tell our form we're doing piecewise. Activates
    # certain things in the rendering proccess
    g_context = {'piecewise': True, 'ajax': True}

    # Set a simple title for the form
    title = 'User signup <small>(not really)</small>'

    first = EntryNode(title="First Name", validators=MaxLengthValidator(32))
    last = EntryNode(title="Last Name", validators=MaxLengthValidator(32))
    password = PasswordNode(title='Password*',
                            validators=MinMaxValidator(5, 32))
    password_confirm = PasswordNode(
        title='Password Confirm*',
        validators=MinMaxValidator(5, 32)
    )

    # Setup a password validator that requires two matching fields
    _passwords_match = Check(MatchingValidator(),
                             'password',
                             'password_confirm')
    email = EntryNode(validators=EmailValidator(), title='Email*')
    address = EntryNode()
    state = ListNode(items=vals.states)
    zip = EntryNode(
        title="Zipcode*",
        validators=[
            IntegerValidator(),
            MinMaxValidator(5, 5)
        ]
    )
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


class Root(Controller):

    def index(self):
        return render_template('index.html')

    def basic(self, *args, **kwargs):
        # Create an instance of our Form class
        form = BasicForm()

        # Handle submission of the form
        if self.request.method == 'POST':
            # Run our convenience method designed for regular forms
            # success is boolean if validation passed, out is the re-rendering of
            # the form
            success, out = form.validate_render(kwargs)
            # This is where actions should be taken on the form
            if success:
                print "Whoo! We should do some sort of database stuff here..."
        else:
            # By default we just render an empty form
            out = form.render()

        def success_header_generate(self):
            return {'message': 'Thanks for your submission!'}

        return render_template('basic.html', form=out)

    def dynamic(self, *args, **kwargs):
        # Handle submission of the form
        if self.request.method == 'POST':
            # This may be a bit confusing. Essentially we're using the data
            # submitted with the request to build our object representation of the
            # form. This is the magic of dynamic forms that allows them to match a
            # changing form based on parameters
            form = DynamicForm.get_form_from_data(kwargs)
            # Then we validate the form just like the old AJAX form
            success, output = form.json_validate(kwargs)
            if success:
                print (
                    "Yay! Successfully validated. Some other actions should be "
                    " taken here..."
                )
            return output

        # Generate the form as default if there's no submission
        form_out = DynamicForm.get_form().render()

        return render_template('dynamic.html', form=form_out)

    def piecewise(self, *args, **kwargs):
        # Generate a regular form via a classmethod to provide easy access to extra
        # functionality
        form = JsonForm()

        # Handle regular submission of the form
        if self.request.method == 'POST':
            success, out = form.json_validate(kwargs, piecewise=True)
            if success:
                print "Whoo! We should do some sort of database stuff here..."

            return out
        else:
            out = form.render()

        return render_template('piecewise.html', form=out)

app = Server(("0.0.0.0", 9000))

from circuits import Debugger
Debugger().register(app)

Static().register(app)
Root().register(app)

app.run()
