const { createApp } = Vue;

createApp({

    data() {

        return {

            stats: {
                total_treks: 0,
                total_users: 0,
                total_staff: 0,
                total_bookings: 0
            },

            treks: [],
            users: [],
            staff: [],
            bookings: [],

            trekSearch: "",
            userSearch: "",

            showTrekModal: false,
            editingTrek: false,

            trekForm: {
                id: null,
                name: "",
                location: "",
                difficulty: "Easy",
                duration: 1,
                available_slots: 0,
                status: "open",
                start_date: "",
                end_date: "",
                description: ""
            },

            message: "",
            messageType: "success"

        };

    },


    mounted() {

        this.loadAll();

    },


    methods: {

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


        async loadAll() {

            await Promise.all([
                this.loadStats(),
                this.loadTreks(),
                this.loadUsers(),
                this.loadStaff(),
                this.loadBookings()
            ]);

        },


        async loadStats() {

            try {

                this.stats =
                    await this.api(
                        "/api/admin/stats"
                    );

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async loadTreks() {

            try {

                let url = "/api/admin/treks";

                if (this.trekSearch) {

                    url +=
                        "?q=" +
                        encodeURIComponent(
                            this.trekSearch
                        );

                }

                const data =
                    await this.api(url);

                this.treks = data.treks;

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async loadUsers() {

            try {

                let url = "/api/admin/users";

                if (this.userSearch) {

                    url +=
                        "?q=" +
                        encodeURIComponent(
                            this.userSearch
                        );

                }

                const data =
                    await this.api(url);

                this.users = data.users;

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async loadStaff() {

            try {

                const data =
                    await this.api(
                        "/api/admin/staff"
                    );

                this.staff = data.staff;

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async loadBookings() {

            try {

                const data =
                    await this.api(
                        "/api/admin/bookings"
                    );

                this.bookings =
                    data.bookings;

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        openCreateTrek() {

            this.editingTrek = false;

            this.trekForm = {

                id: null,
                name: "",
                location: "",
                difficulty: "Easy",
                duration: 1,
                available_slots: 0,
                status: "open",
                start_date: "",
                end_date: "",
                description: ""

            };

            this.showTrekModal = true;

        },


        editTrek(trek) {

            this.editingTrek = true;

            this.trekForm = {
                ...trek
            };

            this.showTrekModal = true;

        },


        async saveTrek() {

            try {

                let url;
                let method;

                if (this.editingTrek) {

                    url =
                        `/api/admin/treks/${this.trekForm.id}`;

                    method = "PUT";

                } else {

                    url =
                        "/api/admin/treks";

                    method = "POST";

                }

                await this.api(
                    url,
                    {
                        method: method,

                        body: JSON.stringify(
                            this.trekForm
                        )
                    }
                );

                this.showTrekModal = false;

                this.showMessage(
                    "Trek saved successfully",
                    "success"
                );

                await this.loadTreks();
                await this.loadStats();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async deleteTrek(id) {

            if (
                !confirm(
                    "Are you sure you want to delete this trek?"
                )
            ) {

                return;

            }

            try {

                await this.api(
                    `/api/admin/treks/${id}`,
                    {
                        method: "DELETE"
                    }
                );

                this.showMessage(
                    "Trek deleted",
                    "success"
                );

                await this.loadTreks();
                await this.loadStats();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async toggleBlacklist(id) {

            try {

                await this.api(
                    `/api/admin/users/${id}/blacklist`,
                    {
                        method: "POST"
                    }
                );

                this.showMessage(
                    "User status updated",
                    "success"
                );

                await this.loadUsers();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async approveStaff(id) {

            try {

                await this.api(
                    `/api/admin/staff/${id}/approve`,
                    {
                        method: "POST"
                    }
                );

                this.showMessage(
                    "Staff approved",
                    "success"
                );

                await this.loadStaff();

            } catch (error) {

                this.showMessage(
                    error.message,
                    "danger"
                );

            }

        },


        async logout() {

            await this.api(
                "/api/auth/logout",
                {
                    method: "POST"
                }
            );

            window.location.href = "/login";

        },


        showMessage(message, type) {

            this.message = message;
            this.messageType = type;

            setTimeout(() => {

                this.message = "";

            }, 3000);

        }

    }

}).mount("#adminApp");