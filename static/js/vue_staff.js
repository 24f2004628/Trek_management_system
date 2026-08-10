const { createApp } = Vue;


createApp({

    data() {

        return {

            treks: [],

            message: "",

            messageType: "success"

        };

    },


    mounted() {

        this.loadTreks();

    },


    methods: {

        // ==========================================
        // API HELPER
        // ==========================================

        async api(url, options = {}) {

            const response = await fetch(url, {

                credentials: "same-origin",

                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },

                ...options

            });


            const data = await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error || "Request failed"
                );

            }


            return data;

        },


        // ==========================================
        // LOAD ASSIGNED TREKS
        // ==========================================

        async loadTreks() {

            try {

                const data =
                    await this.api(
                        "/api/staff/treks"
                    );


                this.treks = data.treks;


            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // UPDATE TREK
        // ==========================================

        async updateTrek(trek) {

            try {

                await this.api(
                    `/api/staff/treks/${trek.id}`,

                    {
                        method: "PUT",

                        body: JSON.stringify({

                            available_slots:
                                trek.available_slots,

                            status:
                                trek.status

                        })

                    }
                );


                this.showMessage(
                    "Trek updated successfully.",
                    "success"
                );


                await this.loadTreks();


            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // LOGOUT
        // ==========================================

        async logout() {

            try {

                await this.api(
                    "/api/auth/logout",

                    {
                        method: "POST"
                    }
                );


                window.location.href = "/login";


            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        // ==========================================
        // STATUS BADGE
        // ==========================================

        statusBadge(status) {

            if (status === "open") {

                return "bg-success";

            }

            if (status === "completed") {

                return "bg-primary";

            }

            if (
                status === "closed" ||
                status === "cancelled"
            ) {

                return "bg-danger";

            }

            return "bg-secondary";

        },


        // ==========================================
        // BOOKING BADGE
        // ==========================================

        bookingBadge(status) {

            if (status === "booked") {

                return "bg-success";

            }

            if (status === "completed") {

                return "bg-primary";

            }

            if (status === "cancelled") {

                return "bg-danger";

            }

            return "bg-secondary";

        },


        // ==========================================
        // DATE FORMAT
        // ==========================================

        formatDate(date) {

            if (!date) {

                return "-";

            }

            return new Date(date)
                .toLocaleDateString();

        },


        // ==========================================
        // MESSAGE
        // ==========================================

        showMessage(message, type) {

            this.message = message;

            this.messageType = type;


            setTimeout(() => {

                this.message = "";

            }, 3000);

        }

    }

}).mount("#staffApp");