<?php

namespace App\Orders;

class Order
{
    public function __construct(
        public readonly int $id,
        public readonly string $customer,
        public readonly float $total,
        public readonly \DateTimeImmutable $orderedAt,
    ) {
    }
}
