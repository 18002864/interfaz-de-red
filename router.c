#include "router.h"
#include "frame.h"
#include "lib/list.h"
#include "master.h"
#include "pico/sem.h"
#include "pico/stdio.h"
#include <stdio.h>
#include <stdlib.h>
#include "pico/time.h"
#include "slave.h"

// Include the function definition here
void read_serial_data_and_display() {
    if (stdio_usb_connected() && getchar_timeout_us(0) != PICO_ERROR_TIMEOUT) {
        struct frame *f = malloc(sizeof *f);
        f->to = getchar();
        f->from = getchar();
        f->length = getchar();
        f->header_checksum = getchar();

        uint8_t calculated_checksum = ((f->to + f->from + f->length) ^ 0xFF) + 1;
        if (calculated_checksum != f->header_checksum) {
            printf("Checksum error: received %d, calculated %d\n", f->header_checksum, calculated_checksum);
            free(f);
            return;
        }

        f->data = malloc(f->length);
        for (int i = 0; i < f->length; i++) {
            f->data[i] = getchar();
        }

        printf("Received Frame:\n");
        printf("To: %d\n", f->to);
        printf("From: %d\n", f->from);
        printf("Length: %d\n", f->length);
        printf("Checksum: %d\n", f->header_checksum);
        printf("Data: %s\n", f->data);

        free(f->data);
        free(f);
    }
}

int main(void) {
    stdio_init_all();
    sleep_ms(1000); // Allow time for serial to connect

    slave_init();
    master_init();

    while (1) {
        read_serial_data_and_display(); // Add this line to check serial input and display

        // Existing code in your loop
        struct receive_elem *elem = NULL;

        sem_acquire_blocking(&receive_sema);
        if (!list_empty(&receive_list))
            elem = list_entry(list_pop_front(&receive_list), struct receive_elem, elem);
        sem_release(&receive_sema);

        if (elem != NULL) {
            struct frame *f = elem->f;
            printf("(%d, %d, %d, %d, %s)\n", f->to, f->from, f->length, f->header_checksum, f->data);
            master_propagate(f);

            free(elem->f->data);
            free(elem->f);
            free(elem);
        }

        sleep_ms(10);
    }
}
