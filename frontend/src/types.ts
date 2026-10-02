export interface Customer{customer_id:string;priority_score:number;waiting_time:number;status:string;urgency:string;service_type:string;estimated_service_time:number;arrival_time:string}
export interface NewCustomer{customer_id:string;urgency:string;service_type:string;estimated_service_time:number;arrival_time:string}
export interface Metrics{context:string;customers_waiting:number;average_waiting_time:number;maximum_waiting_time:number;average_service_time:number;throughput:number;queue_length:number}
export interface ContextInfo{name:string;urgency_scores:Record<string,number>;service_types:Record<string,number>}
export interface ComparisonResult{algorithm:string;average_waiting_time:number;maximum_waiting_time:number;average_turnaround_time:number;customers_served:number}
export interface ComparisonResponse{context:string;results:ComparisonResult[]}
