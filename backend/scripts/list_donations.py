import os
import sys
import django


def main():
    # Ensure backend project folder is on PYTHONPATH
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReCo.settings')
    django.setup()

    from marketplace.models import Donation

    qs = Donation.objects.select_related('donor').all()
    print('TOTAL DOAÇÕES:', qs.count())
    for d in qs.order_by('pk'):
        donor = getattr(d, 'donor', None)
        uname = donor.username if donor else '—'
        utype = getattr(getattr(donor, 'profile', None), 'user_type', '—')
        print(f"{d.pk} | {d.title} | donor={uname} ({utype}) | status={d.status} | created={d.created_at}")


if __name__ == '__main__':
    main()
