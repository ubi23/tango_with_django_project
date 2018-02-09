from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm , PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime




def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary
    # that will be passed to the template engine.
    request.session.set_test_cookie()
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    visitor_cookie_handler(request)
    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    context_dict = { 'categories': category_list,
                     'pages': page_list,
                     'visits':request.session['visits']}

    response = render(request, 'rango/index.html', context=context_dict)

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return response
    
def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass
    # to the template rendering engine.
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)

        pages = Page.objects.filter(category=category)
        # Adds our result list to the template context under name pages.
        context_dict['pages'] = pages
        #We also add the category object from
        # the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything -
        # the template will display the "no category" message for us
        context_dict['category'] = None
        context_dict['pages'] = None


    return render(request, 'rango/category.html', context_dict)
                     
@login_required                    
def add_category(request):
	form = CategoryForm()

	# a HTTP POST?
	if request.method == 'POST':
		form = CategoryForm(request.POST)


		# have we been provided with a valid form?
		if form.is_valid():
			# save the new category to the database
			form.save(commit=True)
			return index(request)
		else:
			print(forms.errors)
            
	return render(request, 'rango/add_category.html', {'form':form})



@login_required
def add_page(request, category_name_slug):
	try:
		category = Category.objects.get(slug=category_name_slug)
	except Category.DoesNotExist:
		category = None

	form = PageForm()
	if request.method == 'POST':
		form = PageForm(request.POST)
		if form.is_valid():
			if category:
				page = form.save(commit=False)
				page.category = category
				page.views = 0
				page.save()
				return show_category(request, category_name_slug)
		else:
			print(form.errors)

	context_dict = {'form':form, 'category': category}
	return render(request, 'rango/add_page.html', context_dict)
		

def register(request):

    registered = False


    if request.method == 'POST':

        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)


        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()


            profile = profile_form.save(commit=False)
            profile.user = user


            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']



            profile.save()

            registered = True

        else:
            print(user_form.errors, profile_form.errors)

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()


    return render(request,
                  'rango/register.html',
                  {'user_form':user_form,
                   'profile_form': profile_form,
                   'registered': registered})

def user_login(request):
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)


        if user:

            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                
                return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html', {})

@login_required
def user_logout(request):
    logout(request)
    return render(request,'rango/index.html',{})


@login_required
def restricted(request):
    context_dict = {}
    return render(request, 'rango/restricted.html', context_dict)
        
def about(request):
    
    
    return render(request, 'rango/about.html',context=None)


def visitor_cookie_handler(request):
    # get the number of visits to the site
    # default value is 1
    visits = int(get_server_side_cookie(request,'visits',1))
    last_visit_cookie = get_server_side_cookie(request,
                                        'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')

    # if it's been more than a day since the last visit..
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        
        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie
    # update visits cookie
    request.session['visits'] =  visits

# helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val 
