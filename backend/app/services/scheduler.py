"""
Notification Scheduler Service.

Handles scheduling and sending reminders for street sweeping.
In production, this would integrate with Firebase Cloud Messaging (FCM)
or another push notification service.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Scheduler for street sweeping reminders.

    Runs daily to check for upcoming sweeps and send notifications.
    """

    def __init__(self):
        self.subscriptions: dict = {}

    async def check_and_notify(self):
        """
        Check all subscriptions and send notifications for upcoming sweeps.

        This would typically run as a cron job.
        """
        logger.info("Running daily notification check...")

        # TODO: Fetch subscriptions from database
        # TODO: Get current week of month
        # TODO: Check each subscription for upcoming sweep
        # TODO: Send push notification via FCM

        logger.info("Notification check complete")

    async def send_notification(
        self, subscription_id: str, message: str, method: str = "push"
    ):
        """
        Send a notification to a subscriber.

        Args:
            subscription_id: The subscriber's ID.
            message: The notification message.
            method: The notification method (push, sms, email).
        """
        logger.info(f"Sending {method} notification to {subscription_id}: {message}")

        if method == "push":
            # TODO: Implement Firebase Cloud Messaging
            pass
        elif method == "sms":
            # TODO: Implement Twilio SMS
            pass
        elif method == "email":
            # TODO: Implement email via SendGrid, etc.
            pass

    def get_next_sweep_date(
        self,
        weekday: str,  # Mon, Tues, Wed, Thu, Fri
        week1: bool,
        week2: bool,
        week3: bool,
        week4: bool,
        week5: bool,
    ) -> Optional[datetime]:
        """
        Calculate the next sweeping date based on schedule.

        Args:
            weekday: Day of week (Mon, Tues, Wed, Thu, Fri)
            week1-week5: Which weeks of the month sweep occurs

        Returns:
            datetime of next sweep, or None if no upcoming sweep
        """
        weekday_map = {
            "Mon": 0,
            "Tues": 1,
            "Wed": 2,
            "Thu": 3,
            "Fri": 4,
        }

        target_weekday = weekday_map.get(weekday)
        if target_weekday is None:
            return None

        today = datetime.now()
        current_weekday = today.weekday()
        current_week = (today.day - 1) // 7 + 1

        # Check if today is the target weekday and this is a sweeping week
        if current_weekday == target_weekday:
            week_flag = [week1, week2, week3, week4, week5][current_week - 1]
            if week_flag:
                return today

        # Find next occurrence
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7

        next_date = today + timedelta(days=days_ahead)

        # Check if the week has sweeping
        next_week = (next_date.day - 1) // 7 + 1
        week_flags = [week1, week2, week3, week4, week5]

        if week_flags[next_week - 1]:
            return next_date

        # Check subsequent weeks (up to 4 weeks ahead)
        for i in range(1, 5):
            check_date = next_date + timedelta(weeks=i)
            check_week = (check_date.day - 1) // 7 + 1

            if week_flags[check_week - 1]:
                return check_date

        return None
