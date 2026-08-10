from datetime import datetime
from celery_app import celery


@celery.task
def daily_trek_reminders():

    from app import create_app
    from models.booking import Booking

    app = create_app()

    with app.app_context():

        today = datetime.today().date()

        bookings = Booking.query.all()

        count = 0

        for booking in bookings:

            trek = booking.trek

            if trek and trek.start_date and trek.start_date >= today:

                print(
                    f"[REMINDER] User {booking.user_id}: "
                    f"Upcoming trek '{trek.name}' "
                    f"starts on {trek.start_date}"
                )

                count += 1

        print(
            f"Daily reminder job completed. "
            f"{count} reminder(s) processed."
        )

        return count


@celery.task
def monthly_activity_report():

    from app import create_app
    from models.trek import Trek
    from models.booking import Booking

    app = create_app()

    with app.app_context():

        total_treks = Trek.query.count()

        total_bookings = Booking.query.count()

        completed_treks = Trek.query.filter_by(
            status="completed"
        ).count()

        report = f"""
        MONTHLY TREKKING ACTIVITY REPORT

        Total Treks: {total_treks}
        Total Bookings: {total_bookings}
        Completed Treks: {completed_treks}
        """

        print(report)

        return report

@celery.task
def export_booking_history(user_id):

    from app import create_app
    from models.booking import Booking

    app = create_app()

    with app.app_context():

        bookings = Booking.query.filter_by(
            user_id=user_id
        ).all()

        export_dir = os.path.join(
            app.root_path,
            "exports"
        )

        os.makedirs(
            export_dir,
            exist_ok=True
        )

        filename = f"booking_history_{user_id}.csv"

        filepath = os.path.join(
            export_dir,
            filename
        )

        with open(
            filepath,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "User ID",
                "Trek Name",
                "Location",
                "Booking Status",
                "Start Date",
                "End Date"
            ])

            for booking in bookings:

                trek = booking.trek

                writer.writerow([
                    user_id,
                    trek.name,
                    trek.location,
                    booking.status,
                    trek.start_date,
                    trek.end_date
                ])

        return filepath