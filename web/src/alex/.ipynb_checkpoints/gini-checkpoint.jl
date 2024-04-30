    
    
import JSON

function expand(indivs::Vector{Tuple{Float64, Int64}})::Vector{Float64}
    
    
    count_sum = 0
    for (agi, count) in indivs
        count_sum += count
    end
    
    v = Vector{Float64}(undef, count_sum)
    i = 1
    
    for (agi, count) in indivs
        for _ in 0:count
            v[i] = agi
            return v
        end
    end

    return v
end

function gini(indivs::Vector{Float64})::Nothing
    n = length(indivs)    
    
    non_neg = filter(n -> n >= 0, indivs)
    T_a = sum(non_neg)
    neg = filter(n -> n < 0, indivs)
    abs_neg = map(n -> abs(n), neg)
    
    T_n = sum(abs_neg)

    s::BigFloat = 0.0
    for i in indivs
        s += i
    end
    avg = s / n
    
    abs_sum::BigFloat = 0
    println("Summing differences")
    loop = 0
    copy_in = copy(indivs)
    for i in 1:length(indivs)
        copy_in .= indivs
        loop += 1
        # println("loop")
        # println(loop)
        ii::Float64 = indivs[i]
        copy_in .- ii
        
        map!( e -> abs(e), copy_in, copy_in)
        abs_sum += sum(copy_in)
    end
    
    g = abs_sum / (2 * (n-1) * (T_a - T_n))
    println(abs_sum)
    println(g)
    return 
end

function main()
    ct = JSON.parsefile("./county_tax.json")
    d = Dict{Int64, Vector{Tuple{Float64, Int64}}}()
    for (k, v) in ct
        new = map(a -> (a[1], a[2]), v)
        d[parse(Int64, k)] = new
        break
    end


    for (k, v) in d
        new = map(a -> (a[1], a[2]), v)
        println(new)
        println(typeof(new))
        expanded = expand(new)
        gini(expanded)
        break
    end

end

main()