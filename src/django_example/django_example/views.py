from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django_example.models import Choice, Poll
from django.shortcuts import redirect
import yota
import datetime
from yota.nodes import *
from yota.validators import *
# We need this to exempt the views. No CSRf support yet
from django.views.decorators.csrf import csrf_exempt


def main_index(request):
    return render_to_response('polls/main-index.html', {})

# Build a simple form for adding polls
class AddPoll(yota.Form):
    title = EntryNode(title="Question", validators=[MinLengthValidator(5),
                                                   MaxLengthValidator(200)])
    submit = SubmitNode(title="Add")


# Build a simple form for adding choices to polls
class AddChoice(yota.Form):
    @classmethod
    def get_choice(cls, polls):
        """ Create a simple form generator the populates the choices from a
        list of Poll objects """

        cl = cls()
        items = []
        for poll in polls:
            items.append((poll.id, poll.question))

        setattr(cl.poll, 'items', items)
        return cl

    poll = ListNode(title="Parent Poll")
    choice = EntryNode(title="Choice", validators=[MinLengthValidator(5),
                                                   MaxLengthValidator(200)])
    submit = SubmitNode(title="Submit")

@csrf_exempt
def add_choice(request, poll_id=None):
    latest_poll_list = Poll.objects.all().order_by('-pub_date')
    form = AddChoice.get_choice(latest_poll_list)
    if poll_id:
        form.poll.data = int(poll_id)

    if request.method == "POST":
        success, output = form.validate_render(request.POST)
        if success:
            # add our new poll question
            c = Choice(poll=Poll.objects.get(id=request.POST['poll']),
                   choice=request.POST['choice'],
                   votes=0)
            c.save()
            return redirect('/')
        else:
            # we want to redisplay the errors
            basic_form_out = output
    else:
        basic_form_out = form.render()

    return render_to_response('polls/add_poll.html', {'form': basic_form_out})

@csrf_exempt
def add_poll(request):
    form = AddPoll()
    if request.method == "POST":
        success, output = form.validate_render(request.POST)
        if success:
            # add our new poll question
            poll = Poll(question=request.POST['title'],
                        pub_date = datetime.date.today())
            poll.save()
            return redirect('/')
        else:
            # we want to redisplay the errors
            basic_form_out = output
    else:
        basic_form_out = form.render()

    return render_to_response('polls/add_poll.html', {'form': basic_form_out})

def index(request):
    latest_poll_list = Poll.objects.all().order_by('-pub_date')[:5]
    return render_to_response('polls/index.html', {'latest_poll_list': latest_poll_list})

def detail(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    return render_to_response('polls/detail.html', {'poll': p})

@csrf_exempt
def vote(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the poll voting form.
        return render_to_response('polls/detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('django_example.views.results', args=(p.id,)))

def results(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    return render_to_response('polls/results.html', {'poll': p})
