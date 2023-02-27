from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile,Post,LikePost,followersCount
from django.http import HttpResponse
from itertools import chain
import random

# Create your views here.
@login_required(login_url='signin')
def index(request):
    print(request.user.username)
    user_obj = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user = user_obj)

    user_following_list = []
    feed = []

    user_following = followersCount.objects.filter(follower = request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user = usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    # user suggestion
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username = user.user)
        user_following_all.append(user_list)

    #POINT OF ERROR
    new_suggestions_list = [x for x in list(all_users) if(x not in list(user_following_all))]
    current_user = User.objects.filter(username = request.user.username)
    final_suggestion_list = [ x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestion_list)

    suggested_username_profile = []
    username_profile_list = []

    for users in final_suggestion_list:
        suggested_username_profile.append(users.id)
    
    for ids in suggested_username_profile:
        profile_list = Profile.objects.filter(user_id = ids)
        username_profile_list.append(profile_list)

    suggested_username_profile_list = list(chain(*username_profile_list))

    return render(request, 'index.html', {'user_profile': user_profile, 'posts':feed_list,'suggested_username_profile_list':suggested_username_profile_list[:4]})

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(email = email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username = username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username = username, email = email, password = password)
                user.save()

                user_login = auth.authenticate(username = username, password = password)
                auth.login(request, user_login)

                user_model = User.objects.get(username = username)
                new_profile = Profile.objects.create(user=user_model, user_id = user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'password not matching')
            return redirect('signup')
    else: 
        return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = auth.authenticate(username=username, password = password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('signin')
    else: 
        return render(request, 'signin.html')

# IMP
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url='signin')
def settings(request): 
    user_profile = Profile.objects.get(user = request.user)

    if request.method == 'POST':
        if request.FILES.get('image')  == None:
            image = user_profile.profileimage
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimage = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimage = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        return redirect('settings')
    
    return render(request, 'setting.html', {'user_profile': user_profile})

@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user = user, image = image, caption = caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')

    return HttpResponse(request,'Dev')

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    # unqiue
    post_id = request.GET.get('post_id')

    post_obj = Post.objects.get(id = post_id)

    #unique
    like_filter = LikePost.objects.filter(post_id = post_id, username = username).first()

    if like_filter == None:
        new_like  = LikePost.objects.create(post_id = post_id, username = username)
        new_like.save()
        post_obj.no_of_likes = post_obj.no_of_likes + 1
        post_obj.save()
        
        return redirect('/')
    else:
        like_filter.delete()
        post_obj.no_of_likes = post_obj.no_of_likes - 1
        post_obj.save()

        return redirect('/')

#unique
@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username = pk)
    user_profile = Profile.objects.get(user = user_object)
    user_post = Post.objects.filter(user = pk)
    user_post_length = len(user_post)

    follower = request.user.username
    user = pk
    
    if followersCount.objects.filter(follower = follower, user = user).first():
        button_text = "Unfollow"
    else:
        button_text = "Follow"
    
    user_follower = followersCount.objects.filter(user = user)
    user_following = len(followersCount.objects.filter(follower = user))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_post': user_post,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'follower_count': user_follower.count(),
        'following_count': user_following

    }
    return render(request, 'profile.html',context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']
        print('Name of follower'+follower)
        print('Name of user'+user)
        
        if followersCount.objects.filter(follower = follower, user = user).first():
            delete_follower = followersCount.objects.get(follower = follower, user = user)
            delete_follower.delete()

            return redirect('/profile/'+user)
        else:
            new_follower = followersCount.objects.create(follower = follower, user = user)
            new_follower.save()

            return redirect('/profile/'+user)
    else:
        return redirect('/')

def god(request):
    return redirect('/settings/')

@login_required(login_url='signin')
def search(request):
    print("username" + request.user.username)
    user_object = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user = user_object)


    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username = username)
    
        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_list = Profile.objects.filter(user_id = ids)
            username_profile_list.append(profile_list)

        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile,'username_profile_list':username_profile_list})