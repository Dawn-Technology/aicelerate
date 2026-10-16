<?php

namespace App\Export;

use App\Orders\Order;

class CsvExporter
{
    /** @param Order[] $orders */
    public function export(array $orders): string
    {
        $lines = ["id,customer,total,ordered_at"];
        foreach ($orders as $order) {
            $lines[] = implode(',', [
                $order->id,
                $order->customer,
                number_format($order->total, 2, '.', ''),
                $order->orderedAt->format('m/d/Y'),
            ]);
        }

        return implode("\n", $lines) . "\n";
    }
}
