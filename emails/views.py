import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import EmailLog, SenderAccount
from .forms import ComposeEmailForm
from .tasks import send_batch_task, retry_failed_batch


def staff_required(u):
    return u.is_active and u.is_staff


@user_passes_test(staff_required, login_url='/login/')
def compose_email(request):
    if request.method == 'POST':
        form = ComposeEmailForm(request.POST)
        if form.is_valid():
            recipients = form.get_recipients()
            batch_id = uuid.uuid4()
            batch_label = form.cleaned_data['batch_label']
            subject = form.cleaned_data['subject']
            template_name = 'email/generic.html'

            logs = []
            for r in recipients:
                logs.append(EmailLog(
                    batch_id=batch_id,
                    batch_label=batch_label,
                    recipient_email=r['email'],
                    recipient_name=r.get('name', ''),
                    subject=subject,
                    template_name=template_name,
                    status='pending',
                    sent_by=request.user,
                ))

            EmailLog.objects.bulk_create(logs)

            send_batch_task.delay(str(batch_id))

            count = len(logs)
            messages.success(
                request,
                f'Se programaron {count} correos en el lote '
                f'"{batch_label}". El envío está en progreso.')
            return redirect('email_logs')
    else:
        form = ComposeEmailForm()

    return render(request, 'emails/compose.html', {'form': form})


@user_passes_test(staff_required, login_url='/login/')
def email_logs(request):
    batches = (
        EmailLog.objects
        .values('batch_id', 'batch_label', 'sent_by__email', 'created_at')
        .annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending')),
        )
        .order_by('-created_at')
    )

    return render(request, 'emails/log_list.html', {'batches': batches})


@user_passes_test(staff_required, login_url='/login/')
def email_log_detail(request, batch_id):
    logs = EmailLog.objects.filter(batch_id=batch_id).order_by('created_at')

    stats = logs.aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
        pending=Count('id', filter=Q(status='pending')),
    )

    batch_label = logs.first().batch_label if logs.exists() else ''

    return render(request, 'emails/log_detail.html', {
        'logs': logs,
        'stats': stats,
        'batch_id': batch_id,
        'batch_label': batch_label,
    })


@user_passes_test(staff_required, login_url='/login/')
def email_retry_failed(request, batch_id):
    if request.method == 'POST':
        retry_failed_batch.delay(str(batch_id))
        messages.success(
            request,
            'Reintentando envíos fallidos. '
            'El proceso comenzará en breve.')
    return redirect('email_log_detail', batch_id=batch_id)


@user_passes_test(staff_required, login_url='/login/')
def sender_accounts(request):
    accounts = SenderAccount.objects.all()
    return render(request, 'emails/sender_accounts.html', {
        'accounts': accounts,
    })
