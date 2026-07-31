import time
import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
DELAY_BETWEEN_EMAILS = 1


def get_available_sender():
    """Return the SenderAccount with the most remaining capacity today."""
    from .models import SenderAccount
    accounts = SenderAccount.objects.filter(is_active=True)
    best = None
    best_remaining = -1
    for account in accounts:
        remaining = account.remaining_today()
        if remaining > best_remaining:
            best_remaining = remaining
            best = account
    return best


def send_single_email(email_log, sender_account):
    """Send one email and update the EmailLog record."""
    try:
        html_content = render_to_string(
            email_log.template_name,
            {'subject': email_log.subject, 'message': ''}
        )
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=email_log.subject,
            body=text_content,
            from_email=f"{sender_account.display_name} <{sender_account.email}>",
            to=[email_log.recipient_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        email_log.status = 'sent'
        email_log.sender_account = sender_account
        email_log.sent_at = timezone.now()
        email_log.error_message = ''
        email_log.save(update_fields=[
            'status', 'sender_account', 'sent_at', 'error_message'
        ])
        return True

    except Exception as e:
        email_log.status = 'failed'
        email_log.sender_account = sender_account
        email_log.error_message = str(e)[:1000]
        email_log.save(update_fields=[
            'status', 'sender_account', 'error_message'
        ])
        logger.error(
            f"Error enviando correo a {email_log.recipient_email}: {e}")
        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_batch_task(self, batch_id):
    """
    Process all pending emails for a batch_id.
    Sends in sub-batches of BATCH_SIZE with DELAY_BETWEEN_EMAILS between each.
    Rotates between available SenderAccounts.
    Retries failed emails up to 2 times automatically.
    """
    from .models import EmailLog

    MAX_AUTO_RETRIES = 2

    for attempt in range(MAX_AUTO_RETRIES + 1):
        pending = list(
            EmailLog.objects.filter(
                batch_id=batch_id, status='pending'
            ).order_by('created_at')
        )

        if not pending:
            break

        total = len(pending)
        sent_count = 0
        failed_count = 0

        logger.info(
            f"Batch {batch_id} (attempt {attempt + 1}): "
            f"processing {total} emails.")

        for i in range(0, total, BATCH_SIZE):
            sub_batch = pending[i:i + BATCH_SIZE]
            sender = get_available_sender()

            if sender is None:
                logger.warning(
                    f"Batch {batch_id}: no active sender accounts. "
                    f"Retrying in 5 minutes.")
                self.retry(countdown=300)
                return

            for email_log in sub_batch:
                sender = get_available_sender()
                if sender is None:
                    logger.warning(
                        f"Batch {batch_id}: sender accounts exhausted. "
                        f"Retrying in 5 minutes.")
                    self.retry(countdown=300)
                    return

                success = send_single_email(email_log, sender)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

                time.sleep(DELAY_BETWEEN_EMAILS)

            if i + BATCH_SIZE < total:
                time.sleep(2)

        logger.info(
            f"Batch {batch_id} attempt {attempt + 1}: "
            f"{sent_count} sent, {failed_count} failed.")

        # If there are failures and we haven't exhausted retries,
        # wait and retry the failed ones
        if failed_count > 0 and attempt < MAX_AUTO_RETRIES:
            logger.info(
                f"Batch {batch_id}: {failed_count} failed. "
                f"Retrying in 30 seconds...")
            time.sleep(30)
            # Reset failed emails to pending for retry
            EmailLog.objects.filter(
                batch_id=batch_id, status='failed'
            ).update(status='pending', error_message='', sender_account=None)
        else:
            break

    # Final stats
    final_stats = EmailLog.objects.filter(batch_id=batch_id).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
    )

    logger.info(
        f"Batch {batch_id} completed: "
        f"{final_stats['sent']} sent, {final_stats['failed']} failed "
        f"out of {final_stats['total']}.")

    return final_stats


@shared_task
def retry_failed_batch(batch_id):
    """Retry all failed emails in a batch by resetting them to pending."""
    from .models import EmailLog
    updated = EmailLog.objects.filter(
        batch_id=batch_id, status='failed'
    ).update(status='pending', error_message='', sender_account=None)

    if updated > 0:
        send_batch_task.delay(batch_id)

    return {'reset': updated}


@shared_task
def cleanup_stale_pending():
    """Mark as failed any pending emails older than 24 hours."""
    from .models import EmailLog
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    updated = EmailLog.objects.filter(
        status='pending', created_at__lt=cutoff
    ).update(
        status='failed',
        error_message='Marcado como fallido: pendiente por más de 24 horas'
    )
    return {'cleaned': updated}
