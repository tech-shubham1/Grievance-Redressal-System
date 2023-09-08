from .models import Profile

def has_designation(request): 
    user = request.user
    # if user is superuser, then no need to check designation
    if user.is_superuser:
        return {'has_designation': True}
    has_designation = False
    if user.is_authenticated:
        has_designation = Profile.objects.get(user=user).designation_holder.exists()
    return {'has_designation': has_designation}

